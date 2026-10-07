"""
Admin / Institutional Governance Routes
---------------------------------------
Authoritative control room for User & Faculty Workload Management,
Cohort & Project Clearance, Academic Calendars & Deadline Overrides,
Accreditation Rubrics, At-Risk Telemetry Radar, and Tamper-Proof Audit Trails.
"""

import csv
import io
import json
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify, Response
from flask_login import login_required, current_user

from app.extensions import db, bcrypt
from app.utils.decorators import admin_required, log_activity
from app.utils.helpers import log_audit_event

from app.models.user import User, Role
from app.models.project import Project, Team, TeamMember, Department, AcademicTerm
from app.models.milestone import Milestone, Submission, MilestoneDeadlineOverride
from app.models.evaluation import RubricTemplate, RubricCriteria, EvaluationScore, GradeBoundary, ExternalJuryAssignment
from app.models.feedback import AuditLog, ActivityLog, Notification, SystemSetting
from app.services.evaluation_service import compute_weighted_score, assign_grade
from app.services.milestone_service import calculate_project_progress

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


@admin_bp.before_request
@login_required
@admin_required
def require_admin():
    """Ensure all admin routes require authentication + admin role."""
    pass


# ==============================================================================
# 1. ADMIN DASHBOARD & TELEMETRY SUMMARY
# ==============================================================================
@admin_bp.route('/dashboard')
def dashboard():
    total_projects = Project.query.count()
    active_teams = Team.query.count()
    pending_reviews = Submission.query.filter(Submission.status.in_(['submitted', 'under_review'])).count()
    total_milestones = Milestone.query.count()
    approved_submissions = Submission.query.filter_by(status='approved').count()
    completion_rate = round((approved_submissions / (total_projects * total_milestones) * 100), 1) if (total_projects and total_milestones) else 0

    stats = {
        'total_projects': total_projects,
        'active_teams': active_teams,
        'pending_reviews': pending_reviews,
        'completion_rate': completion_rate
    }
    
    # Active Users Online (seen in last 15 minutes)
    fifteen_mins_ago = datetime.utcnow() - timedelta(minutes=15)
    active_online_users = User.query.filter(User.last_seen_at >= fifteen_mins_ago).all()
    
    departments = Department.get_ordered()
    all_projects = Project.query.all()
    recent_logs = AuditLog.query.order_by(AuditLog.timestamp.desc()).limit(10).all()
    if not recent_logs:
        recent_logs = ActivityLog.query.order_by(ActivityLog.created_at.desc()).limit(10).all()

    # Proposed projects awaiting clearance
    pending_proposals_count = Project.query.filter_by(status='proposed').count()

    # At-risk teams count (<50% progress)
    at_risk_count = 0
    for p in all_projects:
        if calculate_project_progress(p.id) < 50:
            at_risk_count += 1

    return render_template(
        'admin/dashboard.html',
        stats=stats,
        recent_logs=recent_logs,
        active_online_users=active_online_users,
        departments=departments,
        all_projects=all_projects,
        pending_proposals_count=pending_proposals_count,
        at_risk_count=at_risk_count
    )


# ==============================================================================
# 2. USER, IDENTITY & FACULTY WORKLOAD MANAGEMENT (Directive 4.1)
# ==============================================================================
@admin_bp.route('/users')
def manage_users():
    """Master User Directory & Governance with live active status and filters."""
    role_filter = request.args.get('role', 'all').lower()
    search_query = request.args.get('q', '').strip()
    status_filter = request.args.get('status', 'all').lower()

    query = User.query
    if role_filter != 'all':
        query = query.join(Role).filter(Role.role_name == role_filter)

    if status_filter in ('active', 'inactive', 'suspended', 'blacklisted'):
        query = query.filter(User.status == status_filter)
    elif status_filter == 'paused':
        query = query.filter(User.status.in_(['inactive', 'suspended']))

    if search_query:
        query = query.filter(
            (User.first_name.ilike(f'%{search_query}%')) |
            (User.last_name.ilike(f'%{search_query}%')) |
            (User.email.ilike(f'%{search_query}%')) |
            (User.department.ilike(f'%{search_query}%'))
        )

    users = query.order_by(User.id.asc()).all()
    roles = Role.query.all()
    departments = Department.get_ordered()

    fifteen_mins_ago = datetime.utcnow() - timedelta(minutes=15)
    online_count = User.query.filter(User.last_seen_at >= fifteen_mins_ago).count()
    total_users_count = User.query.count()
    active_count = User.query.filter(User.status == 'active').count()
    inactive_count = User.query.filter(User.status == 'inactive').count()
    blacklisted_count = User.query.filter(User.status == 'blacklisted').count()

    return render_template(
        'admin/users.html',
        users=users,
        roles=roles,
        departments=departments,
        current_filter=role_filter,
        search_query=search_query,
        status_filter=status_filter,
        online_count=online_count,
        total_users_count=total_users_count,
        active_count=active_count,
        inactive_count=inactive_count,
        blacklisted_count=blacklisted_count
    )


@admin_bp.route('/users/create', methods=['POST'])
@log_activity('create_user')
def create_user():
    """Admin creates a single user account."""
    first_name = request.form.get('first_name', '').strip()
    last_name = request.form.get('last_name', '').strip()
    email = request.form.get('email', '').strip().lower()
    password = request.form.get('password', 'password123').strip()
    role_name = request.form.get('role', 'student').lower()
    department = request.form.get('department', 'CSE').strip()
    enrollment = request.form.get('enrollment_number', '').strip()

    if not email or not first_name:
        flash('Email and First Name are mandatory.', 'error')
        return redirect(url_for('admin.manage_users'))

    if User.query.filter_by(email=email).first():
        flash(f'User with email {email} already exists.', 'error')
        return redirect(url_for('admin.manage_users'))

    role = Role.query.filter_by(role_name=role_name).first()
    if not role:
        role = Role.query.first()

    new_user = User(
        first_name=first_name,
        last_name=last_name,
        email=email,
        role_id=role.id,
        department=department,
        enrollment_number=enrollment or None,
        is_active=True
    )
    new_user.set_password(password)
    db.session.add(new_user)
    db.session.commit()

    log_audit_event(
        user_id=current_user.id,
        action='create_user',
        entity_type='user',
        entity_id=new_user.id,
        details={'name': new_user.full_name, 'email': email, 'role': role_name}
    )

    flash(f'User {new_user.full_name} ({email}) created successfully.', 'success')
    return redirect(url_for('admin.manage_users'))


@admin_bp.route('/users/bulk-import', methods=['POST'])
@log_activity('bulk_import_users')
def bulk_import_users():
    """Bulk CSV import tool for batch student and faculty roster onboarding."""
    csv_file = request.files.get('csv_file')
    csv_text = request.form.get('csv_text', '').strip()
    default_role = request.form.get('default_role', 'student')

    content = ""
    if csv_file and csv_file.filename:
        content = csv_file.read().decode('utf-8', errors='ignore')
    elif csv_text:
        content = csv_text

    if not content:
        flash('Please upload a CSV file or paste CSV content.', 'error')
        return redirect(url_for('admin.manage_users'))

    reader = csv.reader(io.StringIO(content))
    created_count = 0
    skipped_count = 0

    roles_map = {r.role_name.lower(): r.id for r in Role.query.all()}

    for row_idx, row in enumerate(reader):
        if not row or row_idx == 0 and any(h in row[0].lower() for h in ['email', 'first', 'name']):
            continue  # Skip header
        if len(row) < 2:
            continue

        # Expected format: First Name, Last Name, Email, Role, Department, Enrollment
        fn = row[0].strip()
        ln = row[1].strip() if len(row) > 1 else ''
        em = row[2].strip().lower() if len(row) > 2 else ''
        rl = (row[3].strip().lower() if len(row) > 3 else default_role) or default_role
        dept = row[4].strip() if len(row) > 4 else 'CSE'
        roll = row[5].strip() if len(row) > 5 else ''

        if not em or '@' not in em:
            continue

        if User.query.filter_by(email=em).first():
            skipped_count += 1
            continue

        role_id = roles_map.get(rl, roles_map.get(default_role, 3))
        user = User(
            first_name=fn,
            last_name=ln,
            email=em,
            role_id=role_id,
            department=dept,
            enrollment_number=roll or None,
            is_active=True
        )
        user.set_password('password123')
        db.session.add(user)
        created_count += 1

    db.session.commit()

    log_audit_event(
        user_id=current_user.id,
        action='bulk_user_import',
        details={'created': created_count, 'skipped': skipped_count}
    )

    flash(f'Bulk import completed: {created_count} users created, {skipped_count} duplicates skipped.', 'success')
    return redirect(url_for('admin.manage_users'))


@admin_bp.route('/users/<int:user_id>/reset-password', methods=['POST'])
@log_activity('reset_password')
def reset_password(user_id):
    """Admin manual password reset for user."""
    user = User.query.get_or_404(user_id)
    new_pass = request.form.get('new_password', 'password123').strip()
    user.set_password(new_pass)
    db.session.commit()

    log_audit_event(
        user_id=current_user.id,
        action='admin_password_reset',
        entity_type='user',
        entity_id=user.id,
        details={'target_user': user.email}
    )

    flash(f'Password reset successfully for {user.full_name}.', 'success')
    return redirect(request.referrer or url_for('admin.manage_users'))


@admin_bp.route('/users/<int:user_id>/toggle-status', methods=['POST'])
@log_activity('toggle_user_status')
def toggle_user_status(user_id):
    """Admin toggle user active / inactive state."""
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('You cannot alter the status of your own administrative account.', 'error')
        return redirect(request.referrer or url_for('admin.manage_users'))

    if user.status == 'blacklisted':
        flash('Blacklisted accounts cannot be toggled. Please click Unblock to restore privileges first.', 'warning')
        return redirect(request.referrer or url_for('admin.manage_users'))

    if user.status == 'active':
        user.status = 'inactive'
        user.is_active = False
    else:
        user.status = 'active'
        user.is_active = True
    db.session.commit()

    log_audit_event(
        user_id=current_user.id,
        action='toggle_user_status',
        entity_type='user',
        entity_id=user.id,
        details={'target_user': user.email, 'new_status': user.status}
    )

    flash(f"User {user.full_name} is now marked as {user.status.capitalize()}.", 'info')
    return redirect(request.referrer or url_for('admin.manage_users'))


@admin_bp.route('/users/<int:user_id>/blacklist', methods=['POST'])
@log_activity('blacklist_user')
def blacklist_user(user_id):
    """Permanently lock and blacklist a user account with required reason note."""
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('You cannot blacklist your own administrative account.', 'error')
        return redirect(request.referrer or url_for('admin.manage_users'))

    reason = request.form.get('block_reason', '').strip()
    if not reason:
        reason = 'Administrative security lockout / institutional compliance violation.'

    user.status = 'blacklisted'
    user.is_active = False
    user.block_reason = reason
    user.blocked_at = datetime.utcnow()
    user.blocked_by_admin_id = current_user.id
    db.session.commit()

    log_audit_event(
        user_id=current_user.id,
        action='blacklist_user',
        entity_type='user',
        entity_id=user.id,
        details={
            'target_user': user.email,
            'reason': reason,
            'blocked_at': str(user.blocked_at),
            'action': 'SESSION_TERMINATION_ENFORCED'
        }
    )

    flash(f"Security Action Enforced: User {user.full_name} ({user.email}) has been blacklisted and locked out.", 'danger')
    return redirect(request.referrer or url_for('admin.manage_users'))


@admin_bp.route('/users/<int:user_id>/unblock', methods=['POST'])
@log_activity('unblock_user')
def unblock_user(user_id):
    """Reinstates a blacklisted account back to active status."""
    user = User.query.get_or_404(user_id)
    user.status = 'active'
    user.is_active = True
    user.block_reason = None
    user.blocked_at = None
    user.blocked_by_admin_id = None
    db.session.commit()

    log_audit_event(
        user_id=current_user.id,
        action='unblock_user',
        entity_type='user',
        entity_id=user.id,
        details={'target_user': user.email, 'restored_status': 'active'}
    )

    flash(f"User {user.full_name} has been reinstated and access restored.", 'success')
    return redirect(request.referrer or url_for('admin.manage_users'))


@admin_bp.route('/faculty-workload')
def faculty_workload():
    """Faculty Workload Dashboard: track cohorts per guide and balance mentoring loads."""
    faculties = User.query.join(Role).filter(Role.role_name == 'faculty').all()
    max_quota = int(SystemSetting.get('FACULTY_MAX_COHORTS', 5))

    workload_data = []
    for f in faculties:
        assigned_teams = Team.query.filter_by(guide_id=f.id).all()
        teams_count = len(assigned_teams)
        utilization = round((teams_count / max_quota) * 100, 1) if max_quota > 0 else 0
        evaluated_count = EvaluationScore.query.filter_by(evaluator_id=f.id).count()
        workload_data.append({
            'faculty': f,
            'teams_count': teams_count,
            'team_count': teams_count,
            'teams': assigned_teams,
            'utilization': utilization,
            'load_percentage': utilization,
            'evaluated_count': evaluated_count,
            'is_overallocated': teams_count > max_quota,
            'is_overburdened': teams_count >= max_quota
        })

    return render_template(
        'admin/faculty_workload.html',
        workload_data=workload_data,
        max_quota=max_quota
    )


# ==============================================================================
# 3. COHORT, TEAM & PROJECT PORTFOLIO GOVERNANCE (Directive 4.2)
# ==============================================================================
@admin_bp.route('/teams')
def manage_teams():
    """Visual Cohort & Team Manager: view members, guides, reassign mentors."""
    teams = Team.query.order_by(Team.created_at.desc()).all()
    faculties = User.query.join(Role).filter(Role.role_name == 'faculty', User.is_active == True).all()  # noqa: E712
    departments = Department.get_ordered()
    current_term = AcademicTerm.query.filter_by(is_current=True).first() or AcademicTerm.query.first()

    return render_template(
        'admin/teams.html',
        teams=teams,
        faculties=faculties,
        departments=departments,
        current_term=current_term
    )


@admin_bp.route('/team/<int:team_id>/reassign-guide', methods=['POST'])
@log_activity('reassign_team_guide')
def reassign_team_guide(team_id):
    """Reassign a cohort to an alternate faculty guide."""
    team = Team.query.get_or_404(team_id)
    new_guide_id = request.form.get('new_guide_id')

    if not new_guide_id or not new_guide_id.isdigit():
        flash('Please select a valid faculty guide.', 'error')
        return redirect(url_for('admin.manage_teams'))

    new_guide = User.query.get_or_404(int(new_guide_id))
    old_guide_name = team.guide.full_name if team.guide else 'Unassigned'
    team.guide_id = new_guide.id
    db.session.commit()

    # Notify new guide
    notif = Notification(
        user_id=new_guide.id,
        title='Cohort Reassigned to You',
        message=f'Administrative reassignment: You are now the assigned Chief Guide for Team "{team.team_name}".',
        notification_type='admin',
        related_entity_type='team',
        related_entity_id=team.id
    )
    db.session.add(notif)
    db.session.commit()

    log_audit_event(
        user_id=current_user.id,
        action='reassign_team_guide',
        entity_type='team',
        entity_id=team.id,
        details={'team_name': team.team_name, 'from': old_guide_name, 'to': new_guide.full_name}
    )

    flash(f'Team "{team.team_name}" reassigned to {new_guide.full_name} successfully.', 'success')
    return redirect(request.referrer or url_for('admin.manage_teams'))


@admin_bp.route('/projects/clearance')
def project_clearance():
    """Project Proposal Clearance Desk: approve, reject, or request revision."""
    status_filter = request.args.get('status', 'proposed')
    query = Project.query
    if status_filter != 'all':
        query = query.filter_by(status=status_filter)
    projects = query.order_by(Project.created_at.desc()).all()

    return render_template(
        'admin/project_clearance.html',
        projects=projects,
        current_status=status_filter
    )


@admin_bp.route('/project/<int:project_id>/clearance', methods=['POST'])
@log_activity('project_clearance_decision')
def project_clearance_decision(project_id):
    """Approve, reject, or request revision for project proposal."""
    project = Project.query.get_or_404(project_id)
    decision = request.form.get('decision')  # 'approve', 'revision_requested', 'reject'
    remarks = request.form.get('remarks', '').strip()

    status_map = {
        'approve': 'approved',
        'revision_requested': 'revision_requested',
        'reject': 'rejected'
    }
    new_status = status_map.get(decision, 'approved')

    project.status = new_status
    project.approved_by = current_user.id
    project.approved_at = datetime.utcnow()
    db.session.commit()

    # Notify team members
    for member in project.team.members:
        if member.user_id:
            notif = Notification(
                user_id=member.user_id,
                title=f'Project Proposal {new_status.replace("_", " ").title()}',
                message=f'Administrative Clearance Decision for "{project.title}": {new_status.replace("_", " ").upper()}. Notes: {remarks or "None"}',
                notification_type='admin',
                related_entity_type='project',
                related_entity_id=project.id
            )
            db.session.add(notif)
    db.session.commit()

    log_audit_event(
        user_id=current_user.id,
        action='project_clearance_decision',
        entity_type='project',
        entity_id=project.id,
        details={'decision': new_status, 'remarks': remarks}
    )

    flash(f'Project "{project.title}" marked as {new_status.replace("_", " ").upper()}.', 'success')
    return redirect(request.referrer or url_for('admin.project_clearance'))


# ==============================================================================
# 4. ACADEMIC CALENDARS & DEADLINE OVERRIDES (Directive 4.3)
# ==============================================================================
@admin_bp.route('/terms', methods=['GET', 'POST'])
def manage_terms():
    """Academic Term Manager with start/end locks."""
    if request.method == 'POST':
        term_name = request.form.get('term_name', '').strip()
        start_date_str = request.form.get('start_date')
        end_date_str = request.form.get('end_date')
        is_current = request.form.get('is_current') in ('on', 'true', '1')

        if term_name and start_date_str and end_date_str:
            s_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            e_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()

            if is_current:
                # Unset previous current term
                AcademicTerm.query.update({AcademicTerm.is_current: False})

            term = AcademicTerm(
                term_name=term_name,
                start_date=s_date,
                end_date=e_date,
                is_current=is_current,
                created_by=current_user.id
            )
            db.session.add(term)
            db.session.commit()

            log_audit_event(
                user_id=current_user.id,
                action='create_academic_term',
                entity_type='academic_term',
                entity_id=term.id,
                details={'term_name': term_name}
            )

            flash(f'Academic Term "{term_name}" created successfully.', 'success')
            return redirect(url_for('admin.manage_terms'))

    terms = AcademicTerm.query.order_by(AcademicTerm.start_date.desc()).all()
    return render_template('admin/terms.html', terms=terms)


@admin_bp.route('/milestones', methods=['GET', 'POST'])
def manage_milestones():
    """Milestone Sprint Configurator: institutional phases (M1-M4) & weightages."""
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        order = int(request.form.get('milestone_order', 1))
        weightage = float(request.form.get('weightage_percent', 25.0))
        deadline_str = request.form.get('deadline')
        term_id = int(request.form.get('academic_term_id', 1))

        if title and deadline_str:
            deadline = datetime.strptime(deadline_str, '%Y-%m-%dT%H:%M') if 'T' in deadline_str else datetime.strptime(deadline_str, '%Y-%m-%d')
            ms = Milestone(
                title=title,
                description=description,
                milestone_order=order,
                weightage_percent=weightage,
                deadline=deadline,
                academic_term_id=term_id,
                created_by=current_user.id
            )
            db.session.add(ms)
            db.session.commit()

            log_audit_event(
                user_id=current_user.id,
                action='create_milestone',
                entity_type='milestone',
                entity_id=ms.id,
                details={'title': title, 'weightage': weightage}
            )

            flash(f'Milestone "{title}" configured successfully.', 'success')
            return redirect(url_for('admin.manage_milestones'))

    milestones = Milestone.query.order_by(Milestone.milestone_order.asc()).all()
    terms = AcademicTerm.query.all()
    teams = Team.query.all()
    overrides = MilestoneDeadlineOverride.query.all()

    return render_template(
        'admin/milestones.html',
        milestones=milestones,
        terms=terms,
        teams=teams,
        overrides=overrides
    )


@admin_bp.route('/milestones/extend', methods=['POST'])
@log_activity('grant_deadline_extension')
def grant_deadline_extension():
    """Deadline Exception Override: grant individual team extensions without altering term calendar."""
    milestone_id = int(request.form.get('milestone_id'))
    team_id = int(request.form.get('team_id'))
    extended_deadline_str = request.form.get('extended_deadline')
    reason = request.form.get('reason', '').strip()

    if not extended_deadline_str:
        flash('Extended deadline date and time is required.', 'error')
        return redirect(url_for('admin.manage_milestones'))

    ext_date = datetime.strptime(extended_deadline_str, '%Y-%m-%dT%H:%M') if 'T' in extended_deadline_str else datetime.strptime(extended_deadline_str, '%Y-%m-%d')

    override = MilestoneDeadlineOverride.query.filter_by(milestone_id=milestone_id, team_id=team_id).first()
    if override:
        override.extended_deadline = ext_date
        override.reason = reason
        override.granted_by = current_user.id
    else:
        override = MilestoneDeadlineOverride(
            milestone_id=milestone_id,
            team_id=team_id,
            extended_deadline=ext_date,
            reason=reason,
            granted_by=current_user.id
        )
        db.session.add(override)
    db.session.commit()

    # Notify team
    team = Team.query.get(team_id)
    ms = Milestone.query.get(milestone_id)
    if team:
        for member in team.members:
            if member.user_id:
                notif = Notification(
                    user_id=member.user_id,
                    title='Deadline Extension Granted',
                    message=f'Milestone "{ms.title}" has been granted an administrative deadline extension to {ext_date.strftime("%b %d, %Y")}. Reason: {reason or "Administrative waiver"}',
                    notification_type='admin',
                    related_entity_type='milestone',
                    related_entity_id=milestone_id
                )
                db.session.add(notif)
        db.session.commit()

    log_audit_event(
        user_id=current_user.id,
        action='grant_deadline_extension',
        entity_type='milestone_deadline_override',
        entity_id=override.id,
        details={'team_id': team_id, 'milestone_id': milestone_id, 'extended_to': ext_date.isoformat(), 'reason': reason}
    )

    flash(f'Deadline extension granted for Team "{team.team_name if team else team_id}".', 'success')
    return redirect(request.referrer or url_for('admin.manage_milestones'))


# ==============================================================================
# 5. ACCREDITATION RUBRICS & EVALUATION AUTHORITY (Directive 4.4)
# ==============================================================================
@admin_bp.route('/rubrics', methods=['GET', 'POST'])
def manage_rubrics():
    """Dynamic Rubric Template Builder with 4-tier ABET/NBA performance descriptors."""
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        term_id = request.form.get('academic_term_id')

        if name:
            template = RubricTemplate(
                name=name,
                description=description,
                academic_term_id=int(term_id) if term_id and term_id.isdigit() else None,
                created_by=current_user.id,
                is_active=True
            )
            db.session.add(template)
            db.session.commit()

            log_audit_event(
                user_id=current_user.id,
                action='create_rubric_template',
                entity_type='rubric_template',
                entity_id=template.id,
                details={'name': name}
            )

            flash(f'Rubric Template "{name}" created.', 'success')
            return redirect(url_for('admin.manage_rubrics'))

    templates = RubricTemplate.query.all()
    terms = AcademicTerm.query.all()
    grade_boundaries = GradeBoundary.query.order_by(GradeBoundary.min_percentage.desc()).all()

    return render_template(
        'admin/rubrics.html',
        templates=templates,
        terms=terms,
        grade_boundaries=grade_boundaries
    )


@admin_bp.route('/rubrics/<int:template_id>/add-criterion', methods=['POST'])
@log_activity('add_rubric_criterion')
def add_rubric_criterion(template_id):
    """Add criterion to rubric template with 4-tier descriptors."""
    template = RubricTemplate.query.get_or_404(template_id)
    c_name = request.form.get('criterion_name', '').strip()
    max_marks = float(request.form.get('max_marks', 25.0))
    weightage = float(request.form.get('weightage', 25.0))
    desc = request.form.get('description', '').strip()
    exemplary = request.form.get('exemplary_desc', 'Exemplary mastery, zero architectural defects.')
    proficient = request.form.get('proficient_desc', 'Clear and complete implementation meeting requirements.')
    developing = request.form.get('developing_desc', 'Partial implementation with minor documentation gaps.')
    unsatisfactory = request.form.get('unsatisfactory_desc', 'Significant deficiencies.')

    crit = RubricCriteria(
        rubric_template_id=template.id,
        criterion_name=c_name,
        max_marks=max_marks,
        weightage=weightage,
        description=desc,
        exemplary_desc=exemplary,
        proficient_desc=proficient,
        developing_desc=developing,
        unsatisfactory_desc=unsatisfactory,
        display_order=len(template.criteria) + 1
    )
    db.session.add(crit)
    db.session.commit()

    flash(f'Criterion "{c_name}" added to template "{template.name}".', 'success')
    return redirect(url_for('admin.manage_rubrics'))


@admin_bp.route('/evaluation/<int:submission_id>/override', methods=['POST'])
@log_activity('admin_evaluation_override')
def override_evaluation(submission_id):
    """Master Evaluation Override: re-open locked submissions or manually adjust marks."""
    submission = Submission.query.get_or_404(submission_id)
    override_score = float(request.form.get('override_score', 90.0))
    override_grade = request.form.get('override_grade', 'A+')
    reason = request.form.get('reason', 'Administrative arbitration waiver').strip()
    unlock_submission = request.form.get('unlock_submission') in ('on', 'true', '1')

    # Update or insert master override evaluation score
    score = EvaluationScore.query.filter_by(submission_id=submission.id).first()
    if not score:
        score = EvaluationScore(
            submission_id=submission.id,
            evaluator_id=current_user.id,
            marks_obtained=override_score,
            total_percentage=override_score,
            grade=override_grade,
            is_overridden_by_admin=True,
            override_reason=reason
        )
        db.session.add(score)
    else:
        score.is_overridden_by_admin = True
        score.override_reason = reason
        score.total_percentage = override_score
        score.grade = override_grade

    if unlock_submission:
        submission.status = 'under_review'
    else:
        submission.status = 'approved'

    db.session.commit()

    log_audit_event(
        user_id=current_user.id,
        action='master_evaluation_override',
        entity_type='submission',
        entity_id=submission.id,
        details={'override_score': override_score, 'grade': override_grade, 'reason': reason, 'unlocked': unlock_submission}
    )

    flash(f'Master Evaluation Override applied: {override_score}% ({override_grade}).', 'warning')
    return redirect(request.referrer or url_for('admin.dashboard'))


# ==============================================================================
# 6. AT-RISK TELEMETRY RADAR & ACCREDITATION EXPORTS (Directive 4.5)
# ==============================================================================
@admin_bp.route('/risk-radar')
def risk_radar():
    """At-Risk Cohort Radar: real-time monitor for underperforming or lagging cohorts."""
    all_projects = Project.query.all()
    at_risk_cohorts = []
    healthy_cohorts = []

    for p in all_projects:
        progress = calculate_project_progress(p.id)
        team = p.team
        
        # Check missed or overdue milestones
        milestones = Milestone.query.filter_by(academic_term_id=team.academic_term_id).all() if team else []
        overdue_count = 0
        now = datetime.utcnow()
        for ms in milestones:
            effective_dl = ms.get_effective_deadline(team.id)
            sub = Submission.query.filter_by(project_id=p.id, milestone_id=ms.id).first()
            if effective_dl and now > effective_dl and (not sub or sub.status in ('pending', 'revision_required')):
                overdue_count += 1

        is_risk = (progress < 50) or (overdue_count > 0)
        cohort_info = {
            'project': p,
            'team': team,
            'progress': progress,
            'overdue_count': overdue_count,
            'guide': team.guide.full_name if team and team.guide else 'Unassigned',
            'lead': team.leader.display_name if team and team.leader else 'Lead'
        }
        if is_risk:
            at_risk_cohorts.append(cohort_info)
        else:
            healthy_cohorts.append(cohort_info)

    return render_template(
        'admin/risk_radar.html',
        at_risk_cohorts=at_risk_cohorts,
        healthy_cohorts=healthy_cohorts
    )


@admin_bp.route('/risk-radar/warn/<int:team_id>', methods=['POST'])
@log_activity('dispatch_risk_warning')
def dispatch_risk_warning(team_id):
    """Dispatch 1-click warning notice to at-risk team and faculty mentor."""
    team = Team.query.get_or_404(team_id)
    custom_msg = request.form.get('message', '').strip() or f'Urgent: Team "{team.team_name}" is currently flagged on the institutional Risk Radar for milestone delivery velocity delays.'

    for member in team.members:
        if member.user_id:
            notif = Notification(
                user_id=member.user_id,
                title='⚠️ Institutional Milestone Warning Notice',
                message=custom_msg,
                notification_type='warning',
                related_entity_type='team',
                related_entity_id=team.id
            )
            db.session.add(notif)

    if team.guide_id:
        notif_guide = Notification(
            user_id=team.guide_id,
            title=f'⚠️ Mentorship Advisory: {team.team_name} At-Risk',
            message=f'Administrative notice regarding cohort "{team.team_name}": {custom_msg}',
            notification_type='warning',
            related_entity_type='team',
            related_entity_id=team.id
        )
        db.session.add(notif_guide)

    db.session.commit()

    log_audit_event(
        user_id=current_user.id,
        action='dispatch_risk_warning',
        entity_type='team',
        entity_id=team.id,
        details={'message': custom_msg}
    )

    flash(f'Warning notice dispatched to all members and guide of Team "{team.team_name}".', 'warning')
    return redirect(request.referrer or url_for('admin.risk_radar'))


@admin_bp.route('/analytics')
def analytics():
    """Department-wide analytics, Chart.js telemetry, criteria score bell curve."""
    projects = Project.query.all()
    departments = Department.get_ordered()
    milestones = Milestone.query.order_by(Milestone.milestone_order.asc()).all()

    # Calculate criteria averages
    criteria_stats = []
    all_criteria = RubricCriteria.query.all()
    for crit in all_criteria:
        scores = EvaluationScore.query.filter_by(rubric_criteria_id=crit.id).all()
        if scores:
            avg_m = sum(s.marks_obtained for s in scores) / len(scores)
            criteria_stats.append({
                'name': crit.criterion_name,
                'avg': round(avg_m, 1),
                'max': crit.max_marks,
                'pct': round((avg_m / crit.max_marks * 100), 1) if crit.max_marks else 0
            })

    return render_template(
        'admin/analytics.html',
        projects=projects,
        departments=departments,
        milestones=milestones,
        criteria_stats=criteria_stats
    )


@admin_bp.route('/export/dossier')
def export_dossier():
    """Generate 1-click consolidated ABET/NBA Accreditation Dossier (Printable HTML / CSV)."""
    fmt = request.args.get('format', 'html').lower()
    projects = Project.query.all()

    dossier_data = []
    for p in projects:
        t = p.team
        submissions = Submission.query.filter_by(project_id=p.id).all()
        scores = []
        for s in submissions:
            computed = compute_weighted_score(s.id)
            if computed and computed.get('percentage'):
                scores.append(computed['percentage'])
        avg_score = round(sum(scores) / len(scores), 1) if scores else 0
        overall_grade = assign_grade(avg_score)
        progress = calculate_project_progress(p.id)

        dossier_data.append({
            'project_title': p.title,
            'team_name': t.team_name if t else 'N/A',
            'department': t.department.name if t and t.department else (p.domain or 'CSE'),
            'guide': t.guide.full_name if t and t.guide else 'Unassigned',
            'lead_scholar': t.leader.display_name if t and t.leader else 'N/A',
            'sdg_alignment': p.sdg_alignment or 'SDG 9',
            'progress_pct': progress,
            'avg_score_pct': avg_score,
            'overall_grade': overall_grade,
            'status': p.status
        })

    if fmt == 'csv':
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=[
            'project_title', 'team_name', 'department', 'guide',
            'lead_scholar', 'sdg_alignment', 'progress_pct',
            'avg_score_pct', 'overall_grade', 'status'
        ])
        writer.writeheader()
        writer.writerows(dossier_data)
        return Response(
            output.getvalue(),
            mimetype="text/csv",
            headers={"Content-Disposition": "attachment;filename=ABET_NBA_Accreditation_Dossier_2026.csv"}
        )

    return render_template('admin/dossier_export.html', dossier_data=dossier_data, generated_at=datetime.utcnow())


# ==============================================================================
# 7. SECURITY INVARIANTS & TAMPER-PROOF AUDIT TRAIL (Directive 4.6)
# ==============================================================================
@admin_bp.route('/audit-logs')
def audit_logs():
    """Dedicated Audit Log viewer: chronological, tamper-proof logs of all platform actions."""
    page = request.args.get('page', 1, type=int)
    action_filter = request.args.get('action', 'all')
    user_id = request.args.get('user_id', type=int)

    query = AuditLog.query
    if action_filter != 'all':
        query = query.filter(AuditLog.action.ilike(f'%{action_filter}%'))
    if user_id:
        query = query.filter_by(user_id=user_id)

    logs = query.order_by(AuditLog.timestamp.desc()).paginate(page=page, per_page=25, error_out=False)

    return render_template(
        'admin/audit_logs.html',
        logs=logs,
        action_filter=action_filter
    )


@admin_bp.route('/settings', methods=['GET', 'POST'])
def system_settings():
    """System configuration switches: file upload limits, submission locks, backup controls."""
    if request.method == 'POST':
        max_file_mb = request.form.get('max_file_size_mb', '32')
        allowed_ext = request.form.get('allowed_extensions', 'pdf,zip,docx,pptx')
        submissions_locked = 'true' if request.form.get('submissions_locked') in ('on', 'true', '1') else 'false'
        faculty_quota = request.form.get('faculty_max_cohorts', '5')

        SystemSetting.set('MAX_FILE_SIZE_MB', max_file_mb, 'Maximum upload file size in megabytes')
        SystemSetting.set('ALLOWED_EXTENSIONS', allowed_ext, 'Comma-separated allowed file extensions')
        SystemSetting.set('SUBMISSIONS_LOCKED', submissions_locked, 'Master kill-switch locking all new milestone submissions')
        SystemSetting.set('FACULTY_MAX_COHORTS', faculty_quota, 'Maximum recommended cohorts per faculty mentor')

        log_audit_event(
            user_id=current_user.id,
            action='update_system_settings',
            details={'max_file_mb': max_file_mb, 'locked': submissions_locked, 'faculty_quota': faculty_quota}
        )

        flash('System governance configurations updated successfully.', 'success')
        return redirect(url_for('admin.system_settings'))

    settings = {
        'MAX_FILE_SIZE_MB': SystemSetting.get('MAX_FILE_SIZE_MB', '32'),
        'ALLOWED_EXTENSIONS': SystemSetting.get('ALLOWED_EXTENSIONS', 'pdf,zip,docx,pptx'),
        'SUBMISSIONS_LOCKED': SystemSetting.get('SUBMISSIONS_LOCKED', 'false') == 'true',
        'FACULTY_MAX_COHORTS': SystemSetting.get('FACULTY_MAX_COHORTS', '5')
    }

    return render_template('admin/settings.html', settings=settings)


# ==============================================================================
# 8. PERMISSIONS & DEPARTMENTS LEGACY INTEGRATION
# ==============================================================================
@admin_bp.route('/permissions')
def manage_permissions():
    """Dedicated Access Control & Permission Matrix."""
    faculties = User.query.join(Role).filter(Role.role_name == 'faculty').all()
    students = User.query.join(Role).filter(Role.role_name == 'student').all()
    admins = User.query.join(Role).filter(Role.role_name == 'admin').all()
    fifteen_mins_ago = datetime.utcnow() - timedelta(minutes=15)
    active_online_users = User.query.filter(User.last_seen_at >= fifteen_mins_ago).all()

    return render_template(
        'admin/permissions.html',
        faculties=faculties,
        students=students,
        admins=admins,
        active_online_users=active_online_users
    )


@admin_bp.route('/update-permission/<int:user_id>', methods=['POST'])
@log_activity('update_user_permission')
def update_permission(user_id):
    """Admin updates permission level, evaluation rights, submission rights, or account status."""
    user = User.query.get_or_404(user_id)
    is_active = request.form.get('is_active') in ('on', 'true', '1')
    can_evaluate = request.form.get('can_evaluate') in ('on', 'true', '1')
    can_submit = request.form.get('can_submit') in ('on', 'true', '1')
    permission_level = request.form.get('permission_level', 'standard')

    if permission_level not in ('full', 'standard', 'restricted'):
        permission_level = 'standard'

    user.is_active = is_active
    user.can_evaluate = can_evaluate
    user.can_submit = can_submit
    user.permission_level = permission_level

    log_audit_event(
        user_id=current_user.id,
        action='update_permission',
        entity_type='user',
        entity_id=user.id,
        details={'level': permission_level, 'active': is_active, 'eval': can_evaluate, 'submit': can_submit}
    )

    flash(f"Permissions updated for {user.full_name}.", "success")
    return redirect(request.referrer or url_for('admin.manage_permissions'))


@admin_bp.route('/departments', methods=['GET', 'POST'])
def manage_departments():
    departments = Department.get_ordered()
    faculties = User.query.join(Role).filter(Role.role_name == 'faculty').all()
    return render_template('admin/departments.html', departments=departments, faculties=faculties)
