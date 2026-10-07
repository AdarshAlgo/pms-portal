"""
Student / Team Member Routes
-----------------------------
Handles dynamic project registration, team formation, milestone deliverable submission,
progress telemetry, and rubric feedback inspection.
"""

from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify, current_app
from flask_login import login_required, current_user

from app.extensions import db
from app.utils.decorators import student_required, log_activity
from app.utils.helpers import save_uploaded_file, log_audit_event
from app.models.user import User, Role
from app.models.project import Team, TeamMember, Project, AcademicTerm, Department
from app.models.milestone import Milestone, Submission, MilestoneDeadlineOverride
from app.models.feedback import FeedbackLog, Notification
from app.models.evaluation import EvaluationScore
from app.services.milestone_service import (
    create_submission, calculate_project_progress, get_submission_timeline
)
from app.services.evaluation_service import compute_weighted_score

student_bp = Blueprint('student', __name__, url_prefix='/student')


def _get_student_project():
    """Helper to retrieve the current student's active project via team membership."""
    membership = TeamMember.query.filter_by(user_id=current_user.id).first()
    if not membership:
        return None, None
    team = Team.query.get(membership.team_id)
    project = Project.query.filter_by(team_id=team.id).first() if team else None
    return team, project


@student_bp.before_request
@login_required
@student_required
def require_student():
    """Ensure all student routes require authentication + student role."""
    pass


@student_bp.route('/dashboard')
def dashboard():
    """Student dashboard — project overview, milestone status, progress charts, deadlines."""
    team, project = _get_student_project()

    milestones_data = []
    progress = 0
    upcoming_deadlines = []

    if project:
        # Get standard milestones for the term + custom milestones for this project
        standard_ms = Milestone.query.filter_by(
            academic_term_id=team.academic_term_id,
            is_custom=False
        ).order_by(Milestone.milestone_order).all()

        custom_ms = Milestone.query.filter_by(
            project_id=project.id,
            is_custom=True
        ).order_by(Milestone.milestone_order, Milestone.created_at).all()

        milestones = standard_ms + custom_ms

        for ms in milestones:
            submission = Submission.query.filter_by(
                project_id=project.id,
                milestone_id=ms.id
            ).first()

            score = None
            if submission and submission.status in ('approved', 'under_review'):
                score_data = compute_weighted_score(submission.id)
                if score_data['criteria_scores']:
                    score = score_data

            effective_deadline = ms.get_effective_deadline(team.id)

            milestones_data.append({
                'milestone': ms,
                'submission': submission,
                'score': score,
                'effective_deadline': effective_deadline,
                'has_extension': effective_deadline != ms.deadline
            })

            # Check upcoming deadlines (within 7 days)
            if effective_deadline:
                ms_date = effective_deadline.date() if hasattr(effective_deadline, 'date') else effective_deadline
                days_until = (ms_date - datetime.utcnow().date()).days
                if 0 <= days_until <= 7 and (not submission or submission.status in ('pending', 'revision_required')):
                    upcoming_deadlines.append({
                        'milestone': ms,
                        'days_remaining': days_until,
                        'deadline': effective_deadline
                    })

        progress = calculate_project_progress(project.id)

    # Recent feedback
    recent_feedback = []
    if project:
        submissions = Submission.query.filter_by(project_id=project.id).all()
        sub_ids = [s.id for s in submissions]
        if sub_ids:
            recent_feedback = FeedbackLog.query.filter(
                FeedbackLog.submission_id.in_(sub_ids),
                FeedbackLog.is_private == False  # noqa: E712
            ).order_by(FeedbackLog.created_at.desc()).limit(6).all()

    return render_template(
        'student/dashboard.html',
        team=team,
        project=project,
        milestones_data=milestones_data,
        progress=progress,
        upcoming_deadlines=upcoming_deadlines,
        recent_feedback=recent_feedback
    )


@student_bp.route('/project/register', methods=['GET', 'POST'])
@log_activity('register_project')
def register_project():
    """Register a new project — dynamic team creation, mentor selection, and member addition."""
    team, project = _get_student_project()
    if project:
        flash('You already have a registered project. You can inspect or update it from your dashboard.', 'info')
        return redirect(url_for('student.dashboard'))

    faculties = User.query.join(Role).filter(Role.role_name == 'faculty', User.is_active == True).all()  # noqa: E712
    departments = Department.query.all()
    current_term = AcademicTerm.query.filter_by(is_current=True).first() or AcademicTerm.query.first()

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        abstract = request.form.get('abstract', '').strip()
        objectives = request.form.get('objectives', '').strip()
        domain = request.form.get('domain', '').strip() or request.form.get('category', 'Artificial Intelligence')
        technology_stack = request.form.get('technology_stack', '').strip() or request.form.get('tech_stack', '')
        team_name = request.form.get('team_name', '').strip()
        guide_id = request.form.get('guide_id')
        dept_id = request.form.get('department_id', 1)
        repo_url = request.form.get('repo_url', '').strip()
        sdg_alignment = request.form.get('sdg_alignment', 'SDG 9: Industry, Innovation & Infrastructure')
        submission_mode = request.form.get('submit_mode', 'publish')  # 'draft' or 'publish'

        if not title or not team_name:
            flash('Project title and team name are mandatory fields.', 'error')
            return render_template('student/register_project.html', faculties=faculties, departments=departments, current_term=current_term)

        if not current_term:
            flash('No active academic term found. Contact system administrator.', 'error')
            return render_template('student/register_project.html', faculties=faculties, departments=departments, current_term=current_term)

        # Create Team
        guide_user_id = int(guide_id) if guide_id and guide_id.isdigit() else None
        new_team = Team(
            team_name=team_name,
            academic_term_id=current_term.id,
            department_id=int(dept_id) if str(dept_id).isdigit() else 1,
            guide_id=guide_user_id,
            status='active' if submission_mode == 'publish' else 'draft',
            max_members=4
        )
        db.session.add(new_team)
        db.session.flush()

        # Add Lead Scholar (Current Student)
        leader_member = TeamMember(
            team_id=new_team.id,
            user_id=current_user.id,
            student_name=current_user.full_name,
            student_email=current_user.email,
            roll_number=current_user.enrollment_number or '2026-CSE-001',
            role_in_team='Leader'
        )
        db.session.add(leader_member)

        # Dynamically Add Additional Team Members (multi-input rows)
        member_names = request.form.getlist('member_names[]')
        member_emails = request.form.getlist('member_emails[]')
        member_rolls = request.form.getlist('member_rolls[]')
        member_roles = request.form.getlist('member_roles[]')

        for idx, m_name in enumerate(member_names):
            name_clean = m_name.strip()
            if not name_clean:
                continue
            email_clean = member_emails[idx].strip() if idx < len(member_emails) else ''
            roll_clean = member_rolls[idx].strip() if idx < len(member_rolls) else ''
            role_clean = member_roles[idx].strip() if idx < len(member_roles) else 'Core Developer'

            # Match registered user if exists
            matched_user = User.query.filter_by(email=email_clean).first() if email_clean else None
            user_fk = matched_user.id if matched_user else None

            extra_member = TeamMember(
                team_id=new_team.id,
                user_id=user_fk,
                student_name=name_clean,
                student_email=email_clean,
                roll_number=roll_clean,
                role_in_team=role_clean
            )
            db.session.add(extra_member)

        # Create Project
        new_project = Project(
            team_id=new_team.id,
            title=title,
            abstract=abstract,
            objectives=objectives,
            domain=domain,
            technology_stack=technology_stack,
            sdg_alignment=sdg_alignment,
            repo_url=repo_url,
            created_by=current_user.id,
            status='proposed' if submission_mode == 'publish' else 'draft'
        )
        db.session.add(new_project)
        db.session.commit()

        # Dispatch notification to selected faculty guide
        if guide_user_id:
            notif = Notification(
                user_id=guide_user_id,
                title='New Capstone Team Proposed',
                message=f'Student {current_user.full_name} proposed project "{title}" with team "{team_name}".',
                notification_type='admin',
                related_entity_type='project',
                related_entity_id=new_project.id
            )
            db.session.add(notif)

        # Audit Log
        log_audit_event(
            user_id=current_user.id,
            action='project_registration',
            entity_type='project',
            entity_id=new_project.id,
            details={
                'title': title,
                'team_name': team_name,
                'guide_id': guide_user_id,
                'members_count': 1 + len([m for m in member_names if m.strip()]),
                'mode': submission_mode
            }
        )

        flash(
            'Capstone Project registered successfully!' if submission_mode == 'publish' else 'Project draft saved successfully.',
            'success'
        )
        return redirect(url_for('student.dashboard'))

    return render_template(
        'student/register_project.html',
        faculties=faculties,
        departments=departments,
        current_term=current_term
    )


@student_bp.route('/milestones/custom', methods=['POST'])
@log_activity('create_custom_milestone')
def create_custom_milestone():
    """Student creates a custom milestone linked to their project."""
    team, project = _get_student_project()
    if not project:
        flash('You must register or belong to an active project before proposing custom milestones.', 'error')
        return redirect(url_for('student.dashboard'))

    title = request.form.get('title', '').strip()
    description = request.form.get('description', '').strip()
    proposed_deadline_str = request.form.get('proposed_deadline', '').strip()
    weightage_str = request.form.get('weightage_percent', '10').strip()
    deliverable_type = request.form.get('deliverable_type', 'Report').strip()

    if not title:
        flash('Milestone title is required.', 'error')
        return redirect(url_for('student.dashboard'))

    try:
        weightage = float(weightage_str)
        if weightage <= 0 or weightage > 50:
            flash('Weightage must be between 1% and 50%.', 'error')
            return redirect(url_for('student.dashboard'))
    except ValueError:
        flash('Invalid weightage percentage.', 'error')
        return redirect(url_for('student.dashboard'))

    # Parse proposed deadline
    try:
        proposed_deadline = datetime.strptime(proposed_deadline_str, '%Y-%m-%d')
    except (ValueError, TypeError):
        proposed_deadline = datetime.utcnow() + timedelta(days=21)

    # Validate deadline does not exceed academic term end date
    if team.academic_term and team.academic_term.end_date:
        term_end = datetime.combine(team.academic_term.end_date, datetime.max.time())
        if proposed_deadline > term_end:
            flash(f'Proposed deadline cannot exceed the academic term end date ({team.academic_term.end_date}).', 'error')
            return redirect(url_for('student.dashboard'))

    # Determine next milestone order
    max_order = db.session.query(db.func.max(Milestone.milestone_order))\
        .filter(db.or_(
            db.and_(Milestone.academic_term_id == team.academic_term_id, Milestone.is_custom == False),
            Milestone.project_id == project.id
        )).scalar() or 4

    new_milestone = Milestone(
        title=title,
        description=description,
        milestone_order=max_order + 1,
        academic_term_id=team.academic_term_id,
        deadline=proposed_deadline,
        weightage_percent=weightage,
        is_mandatory=False,
        is_custom=True,
        created_by_student_id=current_user.id,
        project_id=project.id,
        approval_status='pending_review',
        deliverable_type=deliverable_type,
        created_by=current_user.id
    )
    db.session.add(new_milestone)
    db.session.commit()

    # Notify faculty guide
    if team.guide_id:
        notif = Notification(
            user_id=team.guide_id,
            title='Custom Milestone Review Requested',
            message=f'Team "{team.team_name}" requested approval for custom milestone: "{title}" ({weightage}% weightage).',
            notification_type='admin',
            related_entity_type='milestone',
            related_entity_id=new_milestone.id
        )
        db.session.add(notif)
        db.session.commit()

    log_audit_event(
        user_id=current_user.id,
        action='create_custom_milestone',
        entity_type='milestone',
        entity_id=new_milestone.id,
        details={
            'title': title,
            'project_id': project.id,
            'weightage': weightage,
            'deliverable_type': deliverable_type,
            'status': 'pending_review'
        }
    )

    flash(f'Custom milestone "{title}" proposed successfully! Status: Pending Faculty Approval.', 'success')
    return redirect(url_for('student.dashboard'))


@student_bp.route('/submit/<int:milestone_id>', methods=['GET', 'POST'])
@log_activity('submit_milestone')
def submit_milestone(milestone_id: int):
    """Submit deliverables against a specific milestone with file upload and repo verification."""
    milestone = Milestone.query.get_or_404(milestone_id)
    team, project = _get_student_project()

    if not project:
        flash('You need to register or join an active project first.', 'error')
        return redirect(url_for('student.register_project'))

    # Custom milestone approval barrier
    if milestone.is_custom and milestone.approval_status != 'approved':
        flash(f'Custom milestone "{milestone.title}" is currently {milestone.approval_status.replace("_", " ")}. Submissions are only permitted after faculty approval.', 'warning')
        return redirect(url_for('student.dashboard'))

    # Check existing submission
    existing = Submission.query.filter_by(
        project_id=project.id,
        milestone_id=milestone_id
    ).first()

    if existing and existing.status in ('approved', 'under_review') and request.method == 'GET':
        flash(f'Milestone "{milestone.title}" has already been submitted and is {existing.status.replace("_", " ")}.', 'info')
        return redirect(url_for('student.dashboard'))

    effective_deadline = milestone.get_effective_deadline(team.id)

    if request.method == 'POST':
        submission_text = request.form.get('submission_text', '').strip()
        repository_url = request.form.get('repository_url', '').strip() or request.form.get('github_url', '').strip()
        document_url = request.form.get('document_url', '').strip()

        # Handle Drag-and-Drop or direct File Attachment
        uploaded_file = request.files.get('file_attachment')
        if uploaded_file and uploaded_file.filename:
            file_url = save_uploaded_file(uploaded_file, subfolder='submissions')
            if file_url:
                document_url = file_url
            else:
                flash('Uploaded file type not permitted. Allowed: PDF, ZIP, DOCX, PPTX.', 'warning')

        if not submission_text and not repository_url and not document_url:
            flash('Please provide sprint description, a repository URL, or upload a project report.', 'error')
            return render_template(
                'student/submit_milestone.html',
                milestone=milestone,
                existing=existing,
                project=project,
                effective_deadline=effective_deadline
            )

        # Check late submission against effective deadline
        is_late = False
        if effective_deadline:
            is_late = datetime.utcnow() > effective_deadline

        if existing:
            # Resubmission / Update
            existing.submission_text = submission_text or existing.submission_text
            existing.document_url = document_url or existing.document_url
            existing.repository_url = repository_url or existing.repository_url
            existing.status = 'submitted'
            existing.is_late = is_late
            existing.submitted_at = datetime.utcnow()
            existing.version = (existing.version or 1) + 1
            existing.revision_count = (existing.revision_count or 0) + 1
            existing.reviewed_by = None
            existing.reviewed_at = None
            submission_record = existing
        else:
            submission_record = create_submission(
                project_id=project.id,
                milestone_id=milestone_id,
                user_id=current_user.id,
                text=submission_text,
                doc_url=document_url,
                repo_url=repository_url
            )
            submission_record.is_late = is_late
            submission_record.version = 1

        db.session.commit()

        # Recalculate project velocity progress
        new_progress = calculate_project_progress(project.id)

        # Notify guide
        if team.guide_id:
            notif = Notification(
                user_id=team.guide_id,
                title=f'Deliverable Submitted: {milestone.title}',
                message=f'{current_user.full_name} (Team {team.team_name}) submitted milestone deliverables. Status: Under Review.',
                notification_type='submission',
                related_entity_type='submission',
                related_entity_id=submission_record.id
            )
            db.session.add(notif)
            db.session.commit()

        # Log Audit Event
        log_audit_event(
            user_id=current_user.id,
            action='submit_deliverable',
            entity_type='submission',
            entity_id=submission_record.id,
            details={
                'milestone_id': milestone.id,
                'project_id': project.id,
                'version': submission_record.version,
                'is_late': is_late,
                'has_file': bool(document_url),
                'new_progress': new_progress
            }
        )

        flash(
            f'Milestone "{milestone.title}" submitted successfully!{" (Logged as Late Submission)" if is_late else ""}',
            'warning' if is_late else 'success'
        )
        return redirect(url_for('student.dashboard'))

    return render_template(
        'student/submit_milestone.html',
        milestone=milestone,
        existing=existing,
        project=project,
        effective_deadline=effective_deadline
    )


@student_bp.route('/feedback')
def feedback():
    """View complete feedback history and rubric criteria marks across all milestones."""
    team, project = _get_student_project()
    all_feedback = []
    evaluations_summary = []

    if project:
        submissions = Submission.query.filter_by(
            project_id=project.id
        ).order_by(Submission.created_at.desc()).all()

        for sub in submissions:
            feedback_entries = FeedbackLog.query.filter_by(
                submission_id=sub.id,
                is_private=False
            ).order_by(FeedbackLog.created_at.desc()).all()

            eval_data = compute_weighted_score(sub.id) if sub.status in ('approved', 'under_review') else None

            all_feedback.append({
                'submission': sub,
                'milestone': sub.milestone,
                'feedback': feedback_entries,
                'evaluation': eval_data
            })

    return render_template(
        'student/feedback.html',
        project=project,
        team=team,
        all_feedback=all_feedback
    )


@student_bp.route('/progress')
def progress():
    """Detailed progress visualization page with interactive burndown context."""
    team, project = _get_student_project()
    progress_pct = 0
    milestones_data = []

    if project:
        progress_pct = calculate_project_progress(project.id)

        standard_ms = Milestone.query.filter_by(
            academic_term_id=team.academic_term_id,
            is_custom=False
        ).order_by(Milestone.milestone_order).all()

        custom_ms = Milestone.query.filter_by(
            project_id=project.id,
            is_custom=True
        ).order_by(Milestone.milestone_order, Milestone.created_at).all()

        milestones = standard_ms + custom_ms

        for ms in milestones:
            submission = Submission.query.filter_by(
                project_id=project.id,
                milestone_id=ms.id
            ).first()

            score = None
            if submission and submission.status == 'approved':
                score_data = compute_weighted_score(submission.id)
                if score_data['criteria_scores']:
                    score = score_data

            milestones_data.append({
                'milestone': ms,
                'submission': submission,
                'score': score,
                'effective_deadline': ms.get_effective_deadline(team.id)
            })

    return render_template(
        'student/progress.html',
        project=project,
        team=team,
        progress=progress_pct,
        milestones_data=milestones_data
    )
