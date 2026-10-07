"""
Faculty / Project Guide Routes
-------------------------------
Handles team review, rubric-based evaluation, status transitions,
meeting log management, and feedback operations.
"""

from datetime import datetime
from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user

from app.extensions import db
from app.utils.decorators import faculty_required, log_activity
from app.utils.helpers import log_audit_event
from app.models.project import Team, Project, Department
from app.models.milestone import Submission, Milestone
from app.models.evaluation import RubricTemplate, RubricCriteria, EvaluationScore
from app.models.feedback import FeedbackLog, MeetingLog, Notification
from app.services.evaluation_service import compute_weighted_score, save_evaluation, assign_grade
from app.services.milestone_service import update_submission_status, get_submission_timeline, calculate_project_progress

faculty_bp = Blueprint('faculty', __name__, url_prefix='/faculty')


@faculty_bp.before_request
@login_required
@faculty_required
def require_faculty():
    """Ensure all faculty routes require authentication + faculty role."""
    pass


@faculty_bp.route('/dashboard')
def dashboard():
    """Faculty dashboard showing assigned teams, review inbox, and cohort health."""
    # Show assigned teams (or all teams for admin)
    teams = Team.query.all() if current_user.is_admin else Team.query.filter_by(guide_id=current_user.id).all()
    team_ids = [t.id for t in teams]

    # Status filter for deliverables inbox
    filter_status = request.args.get('status', 'all').lower()

    # Deliverables query across assigned teams
    project_ids = [t.project.id for t in teams if t.project]
    submissions_query = Submission.query.filter(Submission.project_id.in_(project_ids)) if project_ids else Submission.query.filter(False)

    if filter_status == 'pending':
        submissions_query = submissions_query.filter(Submission.status.in_(['submitted', 'under_review']))
    elif filter_status in ('submitted', 'under_review', 'approved', 'revision_required'):
        submissions_query = submissions_query.filter_by(status=filter_status)

    inbox_submissions = submissions_query.order_by(Submission.submitted_at.desc()).all() if project_ids else []

    pending_reviews_count = Submission.query.filter(
        Submission.project_id.in_(project_ids),
        Submission.status.in_(['submitted', 'under_review'])
    ).count() if project_ids else 0

    # Upcoming meetings
    upcoming_meetings = MeetingLog.query.filter(
        MeetingLog.scheduled_by == current_user.id,
        MeetingLog.meeting_date >= datetime.utcnow().date(),
        MeetingLog.status == 'scheduled'
    ).order_by(MeetingLog.meeting_date).limit(5).all()

    # Total evaluations conducted
    total_evaluations = EvaluationScore.query.filter_by(
        evaluator_id=current_user.id
    ).count()

    # Analytics across assigned projects
    projects_analytics = []
    total_ms = Milestone.query.count() or 4
    for t in teams:
        if not t.project:
            continue
        p = t.project
        approved_count = Submission.query.filter_by(project_id=p.id, status='approved').count()
        progress_pct = round((approved_count / total_ms) * 100, 1)

        # Average rubric marks
        submissions = Submission.query.filter_by(project_id=p.id).all()
        scores = []
        for s in submissions:
            sc = compute_weighted_score(s.id)
            if sc and sc.get('percentage'):
                scores.append(sc['percentage'])
        avg_score = round(sum(scores) / len(scores), 1) if scores else 0
        lead_member = t.leader.display_name if t.leader else 'Lead'

        projects_analytics.append({
            'id': p.id,
            'title': p.title,
            'team_id': t.id,
            'team_name': t.team_name,
            'lead': lead_member,
            'guide': t.guide.full_name if t.guide else 'Guide',
            'dept': t.department.name if t.department else (p.domain or 'CSE'),
            'progress': progress_pct,
            'avg_score': avg_score,
            'approved_milestones': approved_count
        })

    pending_custom_milestones = Milestone.query.filter(
        Milestone.project_id.in_(project_ids),
        Milestone.is_custom == True,
        Milestone.approval_status == 'pending_review'
    ).order_by(Milestone.created_at.desc()).all() if project_ids else []

    return render_template(
        'faculty/dashboard.html',
        teams=teams,
        inbox_submissions=inbox_submissions,
        pending_reviews=pending_reviews_count,
        pending_custom_milestones=pending_custom_milestones,
        upcoming_meetings=upcoming_meetings,
        total_evaluations=total_evaluations,
        projects_analytics=projects_analytics,
        filter_status=filter_status
    )


@faculty_bp.route('/team/<int:id>')
def team_detail(id: int):
    """Detailed view of a team — project info, milestone statuses, submissions."""
    team = Team.query.get_or_404(id)

    # Verify authorization
    if not current_user.is_admin and team.guide_id != current_user.id:
        flash('You are not authorized to view this team.', 'error')
        return redirect(url_for('faculty.dashboard'))

    milestones_data = []
    if team.project:
        milestones = Milestone.query.filter_by(
            academic_term_id=team.academic_term_id
        ).order_by(Milestone.milestone_order).all()

        for ms in milestones:
            submission = Submission.query.filter_by(
                project_id=team.project.id,
                milestone_id=ms.id
            ).first()
            milestones_data.append({
                'milestone': ms,
                'submission': submission,
                'score': compute_weighted_score(submission.id) if (
                    submission and submission.status in ('approved', 'under_review')
                ) else None,
                'effective_deadline': ms.get_effective_deadline(team.id)
            })

    return render_template(
        'faculty/team_detail.html',
        team=team,
        milestones_data=milestones_data
    )


@faculty_bp.route('/evaluate/<int:submission_id>', methods=['GET', 'POST'])
@log_activity('evaluate_submission')
def evaluate_submission(submission_id: int):
    """Rubric-based evaluation engine — faculty scores each criterion, sets grade, and decides state."""
    submission = Submission.query.get_or_404(submission_id)
    team = submission.project.team

    # Verify authorization
    if not current_user.is_admin and team.guide_id != current_user.id:
        flash('You are not authorized to evaluate this submission.', 'error')
        return redirect(url_for('faculty.dashboard'))

    # Auto-transition to under_review on open
    if submission.status == 'submitted':
        update_submission_status(submission.id, 'under_review', current_user.id)

    # Get active rubric template
    rubric = RubricTemplate.query.filter_by(
        academic_term_id=submission.milestone.academic_term_id,
        is_active=True
    ).first() or RubricTemplate.query.filter_by(is_active=True).first()

    if not rubric:
        flash('No active rubric template found in the system.', 'error')
        return redirect(url_for('faculty.dashboard'))

    criteria = RubricCriteria.query.filter_by(
        rubric_template_id=rubric.id
    ).order_by(RubricCriteria.display_order).all()

    existing_scores = {
        s.rubric_criteria_id: s for s in EvaluationScore.query.filter_by(
            submission_id=submission.id,
            evaluator_id=current_user.id
        ).all()
    }

    if request.method == 'POST':
        raw_decision = (request.form.get('decision') or request.form.get('status') or 'approve').strip().lower()
        decision = 'approve' if raw_decision in ('approve', 'approved') else ('revision_required' if raw_decision in ('revision_required', 'revision') else 'save_draft')
        general_feedback = (request.form.get('feedback') or request.form.get('overall_feedback') or '').strip()
        scores_data = []
        valid = True

        for criterion in criteria:
            marks_key = f'marks_{criterion.id}'
            remarks_key = f'remarks_{criterion.id}'

            marks_value = request.form.get(marks_key, '0')
            remarks_value = request.form.get(remarks_key, '')

            try:
                marks_obtained = float(marks_value)
            except (ValueError, TypeError):
                flash(f'Invalid numeric mark for {criterion.criterion_name}.', 'error')
                valid = False
                break

            if marks_obtained < 0 or marks_obtained > float(criterion.max_marks):
                flash(f'Marks for {criterion.criterion_name} must be between 0 and {criterion.max_marks}.', 'error')
                valid = False
                break

            scores_data.append({
                'rubric_criteria_id': criterion.id,
                'marks_obtained': marks_obtained,
                'remarks': remarks_value
            })

        if valid and scores_data:
            # Save evaluation scores
            computed = save_evaluation(submission_id, current_user.id, scores_data, feedback_summary=general_feedback)

            # Determine new submission status
            if decision == 'approve':
                new_status = 'approved'
                status_label = 'Approved'
            elif decision == 'revision_required':
                new_status = 'revision_required'
                status_label = 'Revision Requested'
            else:
                new_status = 'under_review'
                status_label = 'Draft Saved (Under Review)'

            update_submission_status(submission.id, new_status, current_user.id)
            submission.reviewed_by = current_user.id
            submission.reviewed_at = datetime.utcnow()

            # Persist feedback log
            fb_text = general_feedback if general_feedback else f"Evaluation processed: {computed['percentage']}% ({computed['grade']})."
            feedback_type = 'approval' if decision == 'approve' else ('revision_request' if decision == 'revision_required' else 'advisory_note')
            fb_entry = FeedbackLog(
                submission_id=submission.id,
                author_id=current_user.id,
                feedback_type=feedback_type,
                content=fb_text
            )
            db.session.add(fb_entry)

            # Dispatch notification to all team members
            for member in team.members:
                if member.user_id:
                    notif = Notification(
                        user_id=member.user_id,
                        title=f'Milestone Evaluation {status_label}',
                        message=f'Dr. {current_user.last_name or current_user.first_name} evaluated "{submission.milestone.title}". Score: {computed["percentage"]}% ({computed["grade"]}).',
                        notification_type='feedback',
                        related_entity_type='submission',
                        related_entity_id=submission.id
                    )
                    db.session.add(notif)

            # Recalculate project progress
            calculate_project_progress(submission.project_id)
            db.session.commit()

            # Audit Log
            log_audit_event(
                user_id=current_user.id,
                action='evaluate_submission',
                entity_type='submission',
                entity_id=submission.id,
                details={
                    'decision': decision,
                    'percentage': computed['percentage'],
                    'grade': computed['grade'],
                    'team_id': team.id,
                    'milestone_id': submission.milestone_id
                }
            )

            flash(f'Evaluation successfully processed! Total: {computed["percentage"]}% ({computed["grade"]}) - Status: {status_label}.', 'success')
            return redirect(url_for('faculty.team_detail', id=team.id))

    timeline = get_submission_timeline(submission.id)
    computed_preview = compute_weighted_score(submission.id)

    return render_template(
        'faculty/evaluate.html',
        submission=submission,
        rubric=rubric,
        criteria=criteria,
        existing_scores=existing_scores,
        computed=computed_preview,
        timeline=timeline,
        team=team
    )


@faculty_bp.route('/review/<int:submission_id>', methods=['GET', 'POST'])
@log_activity('review_submission')
def review_submission(submission_id: int):
    """Alias/Quick Review desk redirecting to comprehensive evaluation or quick comments."""
    return redirect(url_for('faculty.evaluate_submission', submission_id=submission_id))


@faculty_bp.route('/reviews')
def reviews():
    """All deliverables inbox for the faculty."""
    return redirect(url_for('faculty.dashboard', status=request.args.get('status', 'all')))


@faculty_bp.route('/meetings', methods=['GET', 'POST'])
def meetings():
    """Manage sprint meetings with assigned teams."""
    teams = Team.query.all() if current_user.is_admin else Team.query.filter_by(guide_id=current_user.id).all()
    
    if request.method == 'POST':
        team_id = request.form.get('team_id')
        meeting_date_str = request.form.get('meeting_date')
        agenda = request.form.get('agenda', '').strip()
        duration = request.form.get('duration_minutes', 30)

        if team_id and meeting_date_str:
            try:
                m_date = datetime.strptime(meeting_date_str, '%Y-%m-%dT%H:%M')
            except ValueError:
                m_date = datetime.utcnow()

            meeting = MeetingLog(
                team_id=int(team_id),
                scheduled_by=current_user.id,
                meeting_date=m_date,
                duration_minutes=int(duration),
                agenda=agenda,
                status='scheduled'
            )
            db.session.add(meeting)
            db.session.commit()

            # Notify team
            selected_team = Team.query.get(int(team_id))
            if selected_team:
                for member in selected_team.members:
                    if member.user_id:
                        notif = Notification(
                            user_id=member.user_id,
                            title='Sprint Advisory Meeting Scheduled',
                            message=f'Dr. {current_user.last_name or current_user.first_name} scheduled a meeting for {m_date.strftime("%b %d, %Y at %I:%M %p")}. Agenda: {agenda}',
                            notification_type='meeting',
                            related_entity_type='meeting',
                            related_entity_id=meeting.id
                        )
                        db.session.add(notif)
                db.session.commit()

            flash('Meeting scheduled successfully!', 'success')
            return redirect(url_for('faculty.meetings'))

    all_meetings = MeetingLog.query.filter_by(scheduled_by=current_user.id).order_by(MeetingLog.meeting_date.desc()).all()
    return render_template('faculty/meetings.html', teams=teams, meetings=all_meetings)


@faculty_bp.route('/my-teams')
def my_teams():
    """Assigned capstone teams overview."""
    teams = Team.query.all() if current_user.is_admin else Team.query.filter_by(guide_id=current_user.id).all()
    return render_template('faculty/my_teams.html', teams=teams)


@faculty_bp.route('/reviews-inbox')
def reviews_inbox():
    """Deliverables review inbox with status filters."""
    teams = Team.query.all() if current_user.is_admin else Team.query.filter_by(guide_id=current_user.id).all()
    project_ids = [t.project.id for t in teams if t.project]
    status_filter = request.args.get('status', 'all').lower()

    query = Submission.query.filter(Submission.project_id.in_(project_ids)) if project_ids else Submission.query.filter(False)
    if status_filter in ('submitted', 'under_review', 'approved', 'revision_required'):
        query = query.filter_by(status=status_filter)

    submissions = query.order_by(Submission.submitted_at.desc()).all() if project_ids else []
    return render_template('faculty/reviews.html', submissions=submissions, status_filter=status_filter)


@faculty_bp.route('/department')
def department_overview():
    """Departmental capstone cohort tracking."""
    departments = Department.get_ordered()
    projects = Project.query.all()
    return render_template('faculty/department.html', departments=departments, projects=projects)


@faculty_bp.route('/milestones')
def milestones_overview():
    """Institutional milestone timelines and evaluation gates."""
    milestones = Milestone.query.order_by(Milestone.milestone_order).all()
    return render_template('faculty/milestones.html', milestones=milestones)


@faculty_bp.route('/rubrics')
def rubrics_matrix():
    """Accreditation rubric criteria matrix."""
    rubrics = RubricTemplate.query.all()
    return render_template('faculty/rubrics.html', rubrics=rubrics)

