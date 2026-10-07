from datetime import datetime
from app.extensions import db
from app.models.milestone import Milestone, Submission
from app.models.feedback import FeedbackLog
from app.models.project import Project

def get_project_milestones(project_id):
    """Returns standard and project-specific custom milestones with submission status."""
    project = Project.query.get_or_404(project_id)
    term_id = project.team.academic_term_id if project.team else None
    
    # 1. Fetch standard global milestones for this academic term
    standard_ms = []
    if term_id:
        standard_ms = Milestone.query.filter_by(
            academic_term_id=term_id, 
            is_custom=False
        ).order_by(Milestone.milestone_order).all()
        
    # 2. Fetch project-specific custom milestones
    custom_ms = Milestone.query.filter_by(
        project_id=project_id, 
        is_custom=True
    ).order_by(Milestone.milestone_order, Milestone.created_at).all()
    
    all_milestones = standard_ms + custom_ms
    
    result = []
    for ms in all_milestones:
        submission = Submission.query.filter_by(project_id=project_id, milestone_id=ms.id).first()
        result.append({
            'milestone': ms,
            'submission': submission,
            'status': submission.status if submission else 'not_started',
            'is_custom': ms.is_custom,
            'approval_status': ms.approval_status,
            'deliverable_type': getattr(ms, 'deliverable_type', 'Report'),
            'faculty_feedback': getattr(ms, 'faculty_feedback', None)
        })
    return result

def create_submission(project_id, milestone_id, user_id, text=None, doc_url=None, repo_url=None, submission_link=None, link_title=None, notes=None):
    """Creates a new submission or updates existing one to submitted."""
    submission = Submission.query.filter_by(project_id=project_id, milestone_id=milestone_id).first()
    
    if not submission:
        submission = Submission(
            project_id=project_id,
            milestone_id=milestone_id,
            submitted_by=user_id
        )
        db.session.add(submission)
        
    primary_link = submission_link or doc_url
    submission.submission_text = text
    submission.submission_link = primary_link
    submission.document_url = primary_link
    submission.link_title = link_title
    submission.notes = notes
    submission.repository_url = repo_url
    submission.status = 'submitted'
    submission.submitted_at = datetime.utcnow()
    
    # Optional: logic for revision count
    db.session.commit()
    return submission

def update_submission_status(submission_id, new_status, reviewer_id, feedback_text=None):
    """Updates submission status and logs feedback."""
    submission = Submission.query.get_or_404(submission_id)
    submission.status = new_status
    submission.reviewed_by = reviewer_id
    submission.reviewed_at = datetime.utcnow()
    
    if new_status == 'revision_required':
        submission.revision_count += 1
        
    if feedback_text:
        log = FeedbackLog(
            submission_id=submission.id,
            author_id=reviewer_id,
            feedback_type='status_update',
            content=feedback_text
        )
        db.session.add(log)
        
    db.session.commit()
    return submission

def get_submission_timeline(submission_id):
    """Returns all feedback and status changes for a submission."""
    feedback = FeedbackLog.query.filter_by(submission_id=submission_id).order_by(FeedbackLog.created_at).all()
    return feedback

def calculate_project_progress(project_id):
    """
    Returns completion percentage based on milestone weightage and submission status.
    Seamlessly integrates standard milestones and approved custom milestones.
    """
    milestones_data = get_project_milestones(project_id)
    if not milestones_data:
        return 0.0
        
    # Active milestones: all standard milestones plus approved custom milestones
    active_milestones = [
        m for m in milestones_data
        if not m['is_custom'] or m['approval_status'] == 'approved'
    ]
    if not active_milestones:
        return 0.0
        
    total_weight = sum(m['milestone'].weightage_percent for m in active_milestones)
    completed_weight = sum(m['milestone'].weightage_percent for m in active_milestones if m['status'] == 'approved')
    
    if total_weight <= 0:
        total = len(active_milestones)
        completed = sum(1 for m in active_milestones if m['status'] == 'approved')
        return round((completed / total) * 100, 1) if total > 0 else 0.0
        
    return round((completed_weight / total_weight) * 100, 1)

def validate_or_normalize_milestone_weights(project_id):
    """
    Validates current milestone weights for a project.
    Returns (total_weight, is_under_or_equal_100).
    """
    milestones_data = get_project_milestones(project_id)
    active_milestones = [
        m['milestone'] for m in milestones_data
        if not m['is_custom'] or m['approval_status'] == 'approved'
    ]
    total_weight = sum(m.weightage_percent for m in active_milestones)
    return total_weight, total_weight <= 100.0
