from app.extensions import db
from app.models.project import Project, Team, Department
from app.models.milestone import Submission, Milestone
from app.services.milestone_service import get_project_milestones, calculate_project_progress
from sqlalchemy import func
from datetime import datetime

def get_project_progress_data(project_id):
    """For Chart.js (milestone completion data)."""
    milestones = get_project_milestones(project_id)
    labels = []
    data = []
    
    cumulative = 0.0
    for m in milestones:
        labels.append(m['milestone'].title)
        if m['status'] == 'approved':
            cumulative += m['milestone'].weightage_percent
        data.append(cumulative)
        
    return {
        'labels': labels,
        'data': data
    }

def get_department_analytics(department_id):
    """Project counts, avg scores."""
    teams = Team.query.filter_by(department_id=department_id).all()
    team_ids = [t.id for t in teams]
    
    projects = Project.query.filter(Project.team_id.in_(team_ids)).all()
    project_count = len(projects)
    
    return {
        'project_count': project_count,
        'active_teams': len(teams)
    }

def get_term_overview(term_id):
    """Overall term statistics."""
    teams = Team.query.filter_by(academic_term_id=term_id).count()
    return {
        'total_teams': teams
    }

def get_milestone_burndown(project_id):
    """Days remaining vs milestones pending."""
    milestones = get_project_milestones(project_id)
    pending_count = sum(1 for m in milestones if m['status'] != 'approved')
    return {
        'pending_count': pending_count
    }
