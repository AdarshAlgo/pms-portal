from flask import Blueprint, jsonify
from flask_login import login_required, current_user
from app.services.analytics_service import get_project_progress_data, get_department_analytics
from app.services.evaluation_service import compute_weighted_score
from app.models.feedback import Notification

api_bp = Blueprint('api', __name__, url_prefix='/api')

@api_bp.route('/progress/<int:project_id>')
@login_required
def get_progress(project_id):
    data = get_project_progress_data(project_id)
    return jsonify(data)

@api_bp.route('/scores/<int:project_id>')
@login_required
def get_scores(project_id):
    """Return evaluation scores for all evaluated milestones of a project (for Chart.js)."""
    from app.models.milestone import Submission, Milestone
    
    submissions = Submission.query.filter_by(project_id=project_id, status='approved').all()
    milestone_labels = []
    percentages = []
    
    for sub in submissions:
        milestone = Milestone.query.get(sub.milestone_id)
        score_data = compute_weighted_score(sub.id)
        if score_data['criteria_scores']:
            milestone_labels.append(milestone.title if milestone else f'Milestone {sub.milestone_id}')
            percentages.append(round(score_data['percentage'], 1))
    
    return jsonify({
        'labels': milestone_labels,
        'scores': percentages,
        'count': len(milestone_labels)
    })

@api_bp.route('/department/<int:dept_id>/stats')
@login_required
def department_stats(dept_id):
    data = get_department_analytics(dept_id)
    return jsonify(data)

@api_bp.route('/notifications')
@login_required
def get_notifications():
    notifications = Notification.query.filter_by(user_id=current_user.id, is_read=False).order_by(Notification.created_at.desc()).all()
    
    from datetime import datetime
    now = datetime.utcnow()
    
    def format_time_ago(dt):
        if not dt:
            return "Just now"
        diff = now - dt
        seconds = diff.total_seconds()
        if seconds < 60:
            return "Just now"
        elif seconds < 3600:
            mins = int(seconds // 60)
            return f"{mins}m ago"
        elif seconds < 86400:
            hrs = int(seconds // 3600)
            return f"{hrs}h ago"
        else:
            days = int(seconds // 86400)
            return f"{days}d ago"

    results = [{
        'id': n.id,
        'title': n.title,
        'message': n.message,
        'notification_type': n.notification_type or 'system',
        'created_at': n.created_at.isoformat(),
        'time_ago': format_time_ago(n.created_at)
    } for n in notifications]

    # If user has no notifications, provide helpful institutional demo alerts so UI is always functional
    if not results:
        role = current_user.role.role_name if current_user.role else 'student'
        if role == 'admin':
            results = [
                {
                    'id': 'sys-1',
                    'title': 'Institutional Milestone Health',
                    'message': 'All 5 cohorts have completed synopsis verification. Mid-term review cycle begins next week.',
                    'notification_type': 'milestone',
                    'time_ago': '1h ago',
                    'is_demo': True
                },
                {
                    'id': 'sys-2',
                    'title': 'Active Telemetry Alert',
                    'message': '10 users currently active across CS, IT, and EC departments.',
                    'notification_type': 'system',
                    'time_ago': '3h ago',
                    'is_demo': True
                }
            ]
        elif role == 'faculty':
            results = [
                {
                    'id': 'sys-1',
                    'title': 'Milestone Submission Ready',
                    'message': 'Agrotech Innovators submitted deliverables for Milestone 3 (Prototype).',
                    'notification_type': 'submission',
                    'time_ago': '45m ago',
                    'is_demo': True
                },
                {
                    'id': 'sys-2',
                    'title': 'Advisory Meeting Scheduled',
                    'message': 'Meeting log recorded for Krishi-Drishti team milestone sprint.',
                    'notification_type': 'meeting',
                    'time_ago': '2h ago',
                    'is_demo': True
                }
            ]
        else:
            results = [
                {
                    'id': 'sys-1',
                    'title': 'Evaluation Graded: A+',
                    'message': 'Dr. Anand Verma completed rubric evaluation for Milestone 2 with 90.0% score.',
                    'notification_type': 'evaluation',
                    'time_ago': '30m ago',
                    'is_demo': True
                },
                {
                    'id': 'sys-2',
                    'title': 'Milestone Deadline Approaching',
                    'message': 'Milestone 4 (Final Presentation & Testing) is due in 14 days.',
                    'notification_type': 'milestone',
                    'time_ago': '5h ago',
                    'is_demo': True
                }
            ]

    return jsonify(results)


@api_bp.route('/notifications/<int:id>/read', methods=['POST'])
@login_required
def mark_notification_read(id):
    notification = Notification.query.get_or_404(id)
    if notification.user_id == current_user.id:
        notification.is_read = True
        from app.extensions import db
        db.session.commit()
        return jsonify({'status': 'success'})
    return jsonify({'error': 'unauthorized'}), 403


@api_bp.route('/notifications/read-all', methods=['POST'])
@login_required
def mark_all_notifications_read():
    Notification.query.filter_by(user_id=current_user.id, is_read=False).update({'is_read': True})
    from app.extensions import db
    db.session.commit()
    return jsonify({'status': 'success', 'message': 'All notifications marked as read'})



# ==============================================================================
# 🤖 VIDYA AI COPILOT API ENDPOINTS
# ==============================================================================

@api_bp.route('/agent/actions')
@login_required
def get_agent_actions():
    """Return available 1-click action chips tailored to current_user role."""
    from app.services.ai_agent_service import get_available_actions_for_user
    actions = get_available_actions_for_user(current_user)
    role_name = current_user.role.role_name if current_user.role else 'student'
    return jsonify({
        'role': role_name,
        'user_name': current_user.full_name,
        'actions': actions
    })


@api_bp.route('/agent/execute', methods=['POST'])
@login_required
def execute_agent_command():
    """Execute either a 1-click preset action or natural language prompt."""
    from flask import request
    from app.services.ai_agent_service import execute_agent_action, process_agent_query

    data = request.get_json(silent=True) or {}
    action_id = data.get('action_id')
    query = data.get('query')

    if action_id:
        html_response = execute_agent_action(current_user, action_id)
    elif query:
        html_response = process_agent_query(current_user, query)
    else:
        html_response = "<p class='text-xs text-slate-500'>Please specify an action or query.</p>"

    return jsonify({
        'status': 'success',
        'html': html_response
    })

