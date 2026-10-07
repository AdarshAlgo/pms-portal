from datetime import datetime
from app.extensions import db
from app.models.evaluation import EvaluationScore, RubricCriteria, GradeBoundary
from app.models.milestone import Submission
from app.models.project import Team, Project

def assign_grade(percentage) -> str:
    """Returns letter grade based on configurable GradeBoundary or default institution scale."""
    try:
        boundaries = GradeBoundary.query.order_by(GradeBoundary.min_percentage.desc()).all()
        if boundaries:
            for b in boundaries:
                if percentage >= b.min_percentage:
                    return b.grade_letter
            return boundaries[-1].grade_letter
    except Exception:
        pass

    # Standard fallback
    if percentage >= 90: return 'A+'
    if percentage >= 80: return 'A'
    if percentage >= 70: return 'B+'
    if percentage >= 60: return 'B'
    if percentage >= 50: return 'C'
    return 'F'

def compute_weighted_score(submission_id: int) -> dict:
    """
    Compute the weighted rubric score for a submission.
    
    For each criterion in the rubric:
      - normalized_score = marks_obtained / max_marks
      - weighted_score = normalized_score * criterion_weightage
    
    Total Score = sum(weighted_scores)
    Total Percentage = (sum(marks_obtained) / sum(max_marks)) * 100
    """
    scores = EvaluationScore.query.filter_by(submission_id=submission_id).all()
    
    criteria_scores = []
    total_obtained = 0.0
    total_max = 0.0
    weighted_total = 0.0
    is_overridden = False
    override_reason = None
    override_grade = None
    
    for score in scores:
        if score.is_overridden_by_admin:
            is_overridden = True
            override_reason = score.override_reason
            if score.grade:
                override_grade = score.grade

        if score.rubric_criteria_id:
            crit = RubricCriteria.query.get(score.rubric_criteria_id)
            if not crit:
                continue
                
            normalized_score = score.marks_obtained / crit.max_marks if crit.max_marks > 0 else 0.0
            weighted_score = normalized_score * crit.weightage
            
            total_obtained += score.marks_obtained
            total_max += crit.max_marks
            weighted_total += weighted_score
            
            criteria_scores.append({
                'criterion_id': crit.id,
                'criterion_name': crit.criterion_name,
                'max_marks': crit.max_marks,
                'marks_obtained': score.marks_obtained,
                'normalized': normalized_score,
                'weighted_score': weighted_score,
                'weightage': crit.weightage,
                'remarks': score.remarks or ''
            })
        
    percentage = (total_obtained / total_max * 100) if total_max > 0 else 0.0
    calculated_grade = assign_grade(percentage)

    return {
        'submission_id': submission_id,
        'criteria_scores': criteria_scores,
        'total_obtained': round(total_obtained, 2),
        'total_max': round(total_max, 2),
        'percentage': round(percentage, 2),
        'weighted_total': round(weighted_total, 2),
        'grade': override_grade or calculated_grade,
        'is_overridden_by_admin': is_overridden,
        'override_reason': override_reason
    }

def save_evaluation(submission_id, evaluator_id, scores: list, feedback_summary: str = None):
    """Saves multiple criteria scores in a transaction and stores summary metrics."""
    for item in scores:
        existing = EvaluationScore.query.filter_by(
            submission_id=submission_id,
            rubric_criteria_id=item['rubric_criteria_id'],
            evaluator_id=evaluator_id
        ).first()
        
        if existing:
            existing.marks_obtained = item['marks_obtained']
            existing.remarks = item.get('remarks', '')
            existing.evaluated_at = datetime.utcnow()
        else:
            new_score = EvaluationScore(
                submission_id=submission_id,
                rubric_criteria_id=item['rubric_criteria_id'],
                evaluator_id=evaluator_id,
                marks_obtained=item['marks_obtained'],
                remarks=item.get('remarks', ''),
                evaluated_at=datetime.utcnow()
            )
            db.session.add(new_score)
            
    db.session.commit()

    # Calculate and store consolidated percentage & grade
    computed = compute_weighted_score(submission_id)
    summary_score = EvaluationScore.query.filter_by(
        submission_id=submission_id,
        evaluator_id=evaluator_id
    ).first()
    if summary_score:
        summary_score.total_percentage = computed['percentage']
        summary_score.grade = computed['grade']
        if feedback_summary:
            summary_score.feedback_summary = feedback_summary
        db.session.commit()

    return computed

def get_team_evaluation_summary(team_id):
    """Aggregate scores across all milestones."""
    project = Project.query.filter_by(team_id=team_id).first()
    if not project:
        return []
        
    submissions = Submission.query.filter_by(project_id=project.id).all()
    summaries = []
    
    for sub in submissions:
        if EvaluationScore.query.filter_by(submission_id=sub.id).first():
            summaries.append(compute_weighted_score(sub.id))
            
    return summaries
