"""
Vidya AI - Intelligent Project Monitoring & Evaluation Copilot
Local grounded intelligence engine with strict Role-Based Access Control (RBAC).
Provides instant 1-click preset actions and role-isolated natural language queries.
"""
from datetime import datetime, timedelta
from flask_login import current_user
from app.extensions import db
from app.models.user import User, Role
from app.models.project import Project, Team, TeamMember, Department
from app.models.milestone import Milestone, Submission
from app.models.evaluation import RubricTemplate, RubricCriteria, EvaluationScore
from app.models.feedback import FeedbackLog, MeetingLog, Notification


def get_available_actions_for_user(user):
    """Return available 1-click quick actions tailored to the user's role."""
    if not user or not user.is_authenticated:
        return [
            {
                "id": "public_overview",
                "label": "🚀 Platform Overview",
                "icon": "fas fa-info-circle",
                "color": "indigo"
            }
        ]

    role_name = user.role.role_name if user.role else "student"

    if role_name == "admin":
        return [
            {
                "id": "admin_audit_risk",
                "label": "🚨 Flag Delayed & At-Risk Projects",
                "icon": "fas fa-exclamation-triangle",
                "color": "rose"
            },
            {
                "id": "admin_live_users",
                "label": "🟢 Audit Live Active Users & Telemetry",
                "icon": "fas fa-users-viewfinder",
                "color": "emerald"
            },
            {
                "id": "admin_dept_overview",
                "label": "📊 Department Milestone Completion",
                "icon": "fas fa-chart-pie",
                "color": "purple"
            },
            {
                "id": "admin_rubrics_matrix",
                "label": "📋 Rubric Templates & Evaluation Health",
                "icon": "fas fa-clipboard-check",
                "color": "indigo"
            }
        ]

    elif role_name == "faculty":
        return [
            {
                "id": "faculty_teams_status",
                "label": "👥 My Assigned Teams & Progress",
                "icon": "fas fa-users",
                "color": "indigo"
            },
            {
                "id": "faculty_pending_inbox",
                "label": "📬 Submissions Pending My Review",
                "icon": "fas fa-inbox",
                "color": "amber"
            },
            {
                "id": "faculty_smart_rubric",
                "label": "✍️ Auto-Draft Rubric Feedback",
                "icon": "fas fa-wand-magic-sparkles",
                "color": "purple"
            },
            {
                "id": "faculty_meeting_audit",
                "label": "📅 Advisory Meetings & Logs Check",
                "icon": "fas fa-calendar-check",
                "color": "emerald"
            }
        ]

    else:  # student
        return [
            {
                "id": "student_project_status",
                "label": "🎯 My Next Milestone & Deadline",
                "icon": "fas fa-flag-checkered",
                "color": "emerald"
            },
            {
                "id": "student_rubric_scores",
                "label": "📈 My Rubric Grades & Scores",
                "icon": "fas fa-chart-line",
                "color": "indigo"
            },
            {
                "id": "student_feedback_logs",
                "label": "💬 Mentor Feedback & Remarks",
                "icon": "fas fa-comment-dots",
                "color": "purple"
            },
            {
                "id": "student_checklist",
                "label": "✅ Pre-Submission Quality Checklist",
                "icon": "fas fa-list-check",
                "color": "teal"
            }
        ]


def execute_agent_action(user, action_id):
    """Execute a 1-click action grounded in the database with strict RBAC."""
    role_name = user.role.role_name if user and user.role else "guest"

    # Admin actions
    if action_id == "admin_audit_risk":
        if role_name != "admin":
            return _unauthorized_response()
        return _admin_audit_risk()

    elif action_id == "admin_live_users":
        if role_name != "admin":
            return _unauthorized_response()
        return _admin_live_users()

    elif action_id == "admin_dept_overview":
        if role_name != "admin":
            return _unauthorized_response()
        return _admin_dept_overview()

    elif action_id == "admin_rubrics_matrix":
        if role_name != "admin":
            return _unauthorized_response()
        return _admin_rubrics_matrix()

    # Faculty actions
    elif action_id == "faculty_teams_status":
        if role_name not in ["faculty", "admin"]:
            return _unauthorized_response()
        return _faculty_teams_status(user)

    elif action_id == "faculty_pending_inbox":
        if role_name not in ["faculty", "admin"]:
            return _unauthorized_response()
        return _faculty_pending_inbox(user)

    elif action_id == "faculty_smart_rubric":
        if role_name not in ["faculty", "admin"]:
            return _unauthorized_response()
        return _faculty_smart_rubric(user)

    elif action_id == "faculty_meeting_audit":
        if role_name not in ["faculty", "admin"]:
            return _unauthorized_response()
        return _faculty_meeting_audit(user)

    # Student actions
    elif action_id == "student_project_status":
        return _student_project_status(user)

    elif action_id == "student_rubric_scores":
        return _student_rubric_scores(user)

    elif action_id == "student_feedback_logs":
        return _student_feedback_logs(user)

    elif action_id == "student_checklist":
        return _student_checklist(user)

    return f"<div class='p-3 bg-slate-100 dark:bg-slate-800 rounded-xl text-xs text-slate-700 dark:text-slate-300'>Action <code>{action_id}</code> is ready.</div>"


def process_agent_query(user, query_text):
    """
    Process natural language or conversational prompts from the user.
    Grounded with real database queries and RBAC restrictions.
    """
    if not query_text or not query_text.strip():
        return "<p class='text-xs text-slate-400'>Please ask a question or select a quick action above.</p>"

    q = query_text.strip().lower()
    role_name = user.role.role_name if user and user.role else "guest"

    # 1. Admin RBAC guard
    if any(k in q for k in ["active user", "online user", "telemetry", "permission", "dean audit", "global rubric"]):
        if role_name != "admin":
            return (
                "<div class='p-3.5 rounded-xl bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-800/40 text-rose-700 dark:text-rose-300 text-xs'>"
                "<div class='font-bold flex items-center mb-1'><i class='fas fa-shield-halved mr-1.5'></i> RBAC Permission Blocked</div>"
                "Institutional telemetry, user permission management, and master administrative audits are exclusively reserved for Admin / Dean credentials."
                "</div>"
            )
        if "user" in q or "online" in q or "active" in q:
            return _admin_live_users()
        if "rubric" in q:
            return _admin_rubrics_matrix()
        return _admin_audit_risk()

    # 2. Risk / Delayed Projects
    if any(k in q for k in ["risk", "delay", "behind", "stuck", "pending review", "late"]):
        if role_name == "admin":
            return _admin_audit_risk()
        elif role_name == "faculty":
            return _faculty_pending_inbox(user)
        else:
            return _student_project_status(user)

    # 3. Rubric & Scores
    if any(k in q for k in ["rubric", "score", "grade", "marks", "evaluation"]):
        if role_name == "faculty":
            return _faculty_smart_rubric(user)
        elif role_name == "student":
            return _student_rubric_scores(user)
        else:
            return _admin_rubrics_matrix()

    # 4. Teams & Project
    if any(k in q for k in ["my team", "team", "project", "milestone", "progress"]):
        if role_name == "faculty":
            return _faculty_teams_status(user)
        elif role_name == "student":
            return _student_project_status(user)
        else:
            return _admin_dept_overview()

    # 5. Feedback & Meetings
    if any(k in q for k in ["feedback", "meeting", "minutes", "remark", "mentor"]):
        if role_name == "faculty":
            return _faculty_meeting_audit(user)
        elif role_name == "student":
            return _student_feedback_logs(user)
        else:
            return _admin_audit_risk()

    # 6. Default Role-Aware Helpful Response
    if role_name == "admin":
        return (
            "<div class='space-y-2.5 text-xs text-slate-700 dark:text-slate-300'>"
            "<p class='font-semibold text-purple-600 dark:text-purple-400 flex items-center'>"
            "<i class='fas fa-robot mr-1.5'></i> Vidya AI Admin Intelligence Assistant"
            "</p>"
            "<p>You can ask me to analyze live system telemetry, flag at-risk cohorts, generate department completion summaries, or inspect global rubric adherence.</p>"
            "<p class='text-[11px] text-slate-500 dark:text-slate-400'>Try clicking <strong>'Flag Delayed & At-Risk Projects'</strong> or <strong>'Audit Live Active Users'</strong> above.</p>"
            "</div>"
        )
    elif role_name == "faculty":
        return (
            "<div class='space-y-2.5 text-xs text-slate-700 dark:text-slate-300'>"
            "<p class='font-semibold text-indigo-600 dark:text-indigo-400 flex items-center'>"
            "<i class='fas fa-robot mr-1.5'></i> Vidya AI Faculty Advisor Assistant"
            "</p>"
            "<p>I can help you monitor your assigned capstone cohorts, identify submissions awaiting your review, auto-draft rubric comments, or check meeting logs.</p>"
            "<p class='text-[11px] text-slate-500 dark:text-slate-400'>Try clicking <strong>'Submissions Pending My Review'</strong> or <strong>'Auto-Draft Rubric Feedback'</strong> above.</p>"
            "</div>"
        )
    else:
        return (
            "<div class='space-y-2.5 text-xs text-slate-700 dark:text-slate-300'>"
            "<p class='font-semibold text-emerald-600 dark:text-emerald-400 flex items-center'>"
            "<i class='fas fa-robot mr-1.5'></i> Vidya AI Student Project Companion"
            "</p>"
            "<p>I am your capstone guide. Ask me about your upcoming milestone deadlines, rubric breakdown, mentor feedback, or pre-submission compliance.</p>"
            "<p class='text-[11px] text-slate-500 dark:text-slate-400'>Try clicking <strong>'My Next Milestone & Deadline'</strong> or <strong>'My Rubric Grades'</strong> above.</p>"
            "</div>"
        )


# ==============================================================================
# 👑 ADMIN ACTIONS (DATABASE GROUNDED)
# ==============================================================================

def _admin_audit_risk():
    """Identify projects that are delayed, behind schedule, or pending approval."""
    projects = Project.query.all()
    milestones = Milestone.query.order_by(Milestone.milestone_order).all()
    total_milestones = len(milestones) or 4

    delayed_projects = []
    normal_projects = []

    for p in projects:
        approved_subs = Submission.query.filter_by(project_id=p.id, status='approved').count()
        progress_pct = int((approved_subs / total_milestones) * 100) if total_milestones else 0
        guide_name = p.team.guide.full_name if (p.team and p.team.guide) else "Unassigned"
        dept_name = p.team.department.name if (p.team and p.team.department) else "General"

        item = {
            "title": p.title,
            "dept": dept_name,
            "guide": guide_name,
            "progress": progress_pct,
            "status": p.status,
            "approved_count": approved_subs
        }

        if progress_pct < 50:
            delayed_projects.append(item)
        else:
            normal_projects.append(item)

    html = [
        "<div class='space-y-3 text-xs'>",
        "<div class='flex items-center justify-between pb-2 border-b border-slate-200 dark:border-white/10'>",
        "  <div class='font-bold text-slate-900 dark:text-white flex items-center'>",
        "    <i class='fas fa-triangle-exclamation text-rose-500 mr-1.5'></i> Institutional Risk & Delay Audit",
        "  </div>",
        f"  <span class='px-2 py-0.5 rounded-full text-[10px] font-bold bg-rose-100 text-rose-700 dark:bg-rose-900/40 dark:text-rose-300'>{len(delayed_projects)} At-Risk Cohorts</span>",
        "</div>"
    ]

    if delayed_projects:
        html.append("<div class='space-y-2'>")
        for dp in delayed_projects:
            html.append(
                f"<div class='p-2.5 rounded-xl bg-rose-50/70 dark:bg-rose-950/30 border border-rose-200 dark:border-rose-900/40'>"
                f"  <div class='flex justify-between items-center mb-1'>"
                f"    <span class='font-bold text-slate-800 dark:text-slate-200'>{dp['title']}</span>"
                f"    <span class='px-1.5 py-0.5 text-[10px] font-bold rounded bg-rose-200 text-rose-800 dark:bg-rose-900/60 dark:text-rose-200'>{dp['progress']}%</span>"
                f"  </div>"
                f"  <div class='text-[11px] text-slate-500 dark:text-slate-400 flex items-center justify-between'>"
                f"    <span><i class='fas fa-building mr-1'></i>{dp['dept']}</span>"
                f"    <span><i class='fas fa-user-tie mr-1'></i>Guide: {dp['guide']}</span>"
                f"  </div>"
                f"  <div class='w-full bg-slate-200 dark:bg-slate-700 h-1.5 rounded-full mt-2 overflow-hidden'>"
                f"    <div class='bg-rose-500 h-full rounded-full' style='width: {dp['progress']}%'></div>"
                f"  </div>"
                f"</div>"
            )
        html.append("</div>")
    else:
        html.append("<p class='text-emerald-600 dark:text-emerald-400'><i class='fas fa-check-circle mr-1'></i> All project cohorts are currently tracking on schedule (>50% completed).</p>")

    html.append(
        "<div class='p-2.5 rounded-xl bg-slate-100 dark:bg-slate-800 text-[11px] text-slate-600 dark:text-slate-400'>"
        "<strong>💡 AI Recommendation:</strong> Issue milestone reminder notifications to guides for cohorts under 50% velocity ahead of semester mid-term reviews."
        "</div>"
    )
    html.append("</div>")
    return "\n".join(html)


def _admin_live_users():
    """Fetch live telemetry of users, active roles, and recent activity."""
    all_users = User.query.all()
    online_users = [u for u in all_users if u.is_online]
    
    admins = [u for u in all_users if u.is_admin]
    faculties = [u for u in all_users if u.is_faculty]
    students = [u for u in all_users if u.is_student]

    html = [
        "<div class='space-y-3 text-xs'>",
        "<div class='flex items-center justify-between pb-2 border-b border-slate-200 dark:border-white/10'>",
        "  <div class='font-bold text-slate-900 dark:text-white flex items-center'>",
        "    <i class='fas fa-satellite-dish text-emerald-500 mr-1.5'></i> Live User Telemetry & Permissions",
        "  </div>",
        f"  <span class='px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300'>{len(online_users)} Online</span>",
        "</div>",
        "<div class='grid grid-cols-3 gap-2 text-center'>",
        f"  <div class='p-2 rounded-xl bg-purple-50 dark:bg-purple-950/40 border border-purple-200 dark:border-purple-800/40'><div class='text-sm font-black text-purple-600 dark:text-purple-400'>{len(admins)}</div><div class='text-[10px] text-slate-500 dark:text-slate-400'>Admins</div></div>",
        f"  <div class='p-2 rounded-xl bg-indigo-50 dark:bg-indigo-950/40 border border-indigo-200 dark:border-indigo-800/40'><div class='text-sm font-black text-indigo-600 dark:text-indigo-400'>{len(faculties)}</div><div class='text-[10px] text-slate-500 dark:text-slate-400'>Faculty</div></div>",
        f"  <div class='p-2 rounded-xl bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-800/40'><div class='text-sm font-black text-emerald-600 dark:text-emerald-400'>{len(students)}</div><div class='text-[10px] text-slate-500 dark:text-slate-400'>Scholars</div></div>",
        "</div>",
        "<div class='font-bold text-slate-700 dark:text-slate-300 mt-2'>Active User Roster:</div>",
        "<div class='space-y-1.5 max-h-48 overflow-y-auto pr-1'>"
    ]

    for u in all_users[:8]:
        status_dot = "<span class='w-2 h-2 rounded-full bg-emerald-500 inline-block mr-1.5'></span>" if u.is_online else "<span class='w-2 h-2 rounded-full bg-slate-300 dark:bg-slate-600 inline-block mr-1.5'></span>"
        perm_badge = f"<span class='text-[9px] px-1.5 py-0.2 rounded bg-slate-200 dark:bg-slate-700 font-mono'>{u.permission_level or 'standard'}</span>"
        html.append(
            f"<div class='flex items-center justify-between p-2 rounded-lg bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700/60 text-[11px]'>"
            f"  <div class='flex items-center'>{status_dot}<span class='font-medium text-slate-800 dark:text-slate-200'>{u.full_name}</span></div>"
            f"  <div class='flex items-center space-x-1.5'><span class='text-[10px] text-slate-500 dark:text-slate-400'>{u.role.role_name if u.role else 'user'}</span>{perm_badge}</div>"
            f"</div>"
        )

    html.append("</div></div>")
    return "\n".join(html)


def _admin_dept_overview():
    """Department performance comparison."""
    depts = Department.query.all()
    milestones = Milestone.query.all()
    total_milestones = len(milestones) or 4

    html = [
        "<div class='space-y-3 text-xs'>",
        "<div class='flex items-center justify-between pb-2 border-b border-slate-200 dark:border-white/10'>",
        "  <div class='font-bold text-slate-900 dark:text-white flex items-center'>",
        "    <i class='fas fa-chart-column text-purple-500 mr-1.5'></i> Department Milestone Velocity",
        "  </div>",
        f"  <span class='px-2 py-0.5 rounded-full text-[10px] font-bold bg-purple-100 text-purple-700 dark:bg-purple-900/40 dark:text-purple-300'>{len(depts)} Departments</span>",
        "</div>"
    ]

    for d in depts:
        dept_teams = Team.query.filter_by(department_id=d.id).all()
        team_ids = [t.id for t in dept_teams]
        dept_projects = Project.query.filter(Project.team_id.in_(team_ids)).all() if team_ids else []
        
        total_proj = len(dept_projects)
        completed_proj = 0
        total_progress = 0

        for p in dept_projects:
            approved = Submission.query.filter_by(project_id=p.id, status='approved').count()
            pct = int((approved / total_milestones) * 100) if total_milestones else 0
            total_progress += pct
            if pct == 100:
                completed_proj += 1

        avg_velocity = int(total_progress / total_proj) if total_proj else 0

        html.append(
            f"<div class='p-2.5 rounded-xl bg-white dark:bg-slate-800/80 border border-slate-200 dark:border-slate-700/80 shadow-sm'>"
            f"  <div class='flex justify-between items-center mb-1'>"
            f"    <span class='font-bold text-slate-800 dark:text-slate-200'>{d.name} ({d.code})</span>"
            f"    <span class='text-[10px] font-bold text-purple-600 dark:text-purple-400'>{avg_velocity}% Avg Velocity</span>"
            f"  </div>"
            f"  <div class='text-[10px] text-slate-500 dark:text-slate-400 mb-1.5'>{total_proj} Projects enrolled &bull; {completed_proj} Completed</div>"
            f"  <div class='w-full bg-slate-200 dark:bg-slate-700 h-1.5 rounded-full overflow-hidden'>"
            f"    <div class='bg-gradient-to-r from-purple-500 to-indigo-500 h-full rounded-full' style='width: {avg_velocity}%'></div>"
            f"  </div>"
            f"</div>"
        )

    html.append("</div>")
    return "\n".join(html)


def _admin_rubrics_matrix():
    """Global rubrics matrix analysis."""
    templates = RubricTemplate.query.all()
    criteria = RubricCriteria.query.all()
    scores = EvaluationScore.query.all()

    html = [
        "<div class='space-y-3 text-xs'>",
        "<div class='flex items-center justify-between pb-2 border-b border-slate-200 dark:border-white/10'>",
        "  <div class='font-bold text-slate-900 dark:text-white flex items-center'>",
        "    <i class='fas fa-clipboard-check text-indigo-500 mr-1.5'></i> Global Rubrics Matrix & Scoring Status",
        "  </div>",
        f"  <span class='px-2 py-0.5 rounded-full text-[10px] font-bold bg-indigo-100 text-indigo-700 dark:bg-indigo-900/40 dark:text-indigo-300'>{len(templates)} Templates Active</span>",
        "</div>",
        "<div class='space-y-2'>"
    ]

    for t in templates:
        crits = RubricCriteria.query.filter_by(rubric_template_id=t.id).order_by(RubricCriteria.display_order).all()
        total_weight = sum([c.weightage for c in crits])
        crit_names = ", ".join([c.criterion_name for c in crits[:3]])
        if len(crits) > 3:
            crit_names += f" +{len(crits)-3} more"

        html.append(
            f"<div class='p-2.5 rounded-xl bg-slate-50 dark:bg-slate-800/80 border border-slate-200 dark:border-slate-700/80'>"
            f"  <div class='flex justify-between items-center'>"
            f"    <span class='font-bold text-slate-800 dark:text-slate-200'>{t.name}</span>"
            f"    <span class='text-[10px] px-2 py-0.5 rounded bg-emerald-100 dark:bg-emerald-900/40 text-emerald-700 dark:text-emerald-300 font-bold'>Weight: {total_weight}%</span>"
            f"  </div>"
            f"  <div class='text-[11px] text-slate-500 dark:text-slate-400 mt-1'>Criteria: {crit_names}</div>"
            f"</div>"
        )

    html.append(
        f"<div class='p-2.5 rounded-xl bg-indigo-50/60 dark:bg-indigo-950/40 border border-indigo-200 dark:border-indigo-900/40 text-[11px] text-indigo-700 dark:text-indigo-300'>"
        f"<i class='fas fa-award mr-1'></i> <strong>Evaluation Volume:</strong> {len(scores)} individual criteria scores currently recorded across all cohorts."
        f"</div>"
        f"</div>"
    )
    return "\n".join(html)


# ==============================================================================
# 👨‍🏫 FACULTY ACTIONS (DATABASE GROUNDED)
# ==============================================================================

def _faculty_teams_status(user):
    """Summarize teams guided by this faculty."""
    guided_teams = Team.query.filter_by(guide_id=user.id).all()
    milestones = Milestone.query.order_by(Milestone.milestone_order).all()
    total_milestones = len(milestones) or 4

    html = [
        "<div class='space-y-3 text-xs'>",
        "<div class='flex items-center justify-between pb-2 border-b border-slate-200 dark:border-white/10'>",
        "  <div class='font-bold text-slate-900 dark:text-white flex items-center'>",
        "    <i class='fas fa-chalkboard-user text-indigo-500 mr-1.5'></i> My Guided Capstone Teams",
        "  </div>",
        f"  <span class='px-2 py-0.5 rounded-full text-[10px] font-bold bg-indigo-100 text-indigo-700 dark:bg-indigo-900/40 dark:text-indigo-300'>{len(guided_teams)} Assigned Teams</span>",
        "</div>"
    ]

    if not guided_teams:
        html.append("<p class='text-slate-500'>You currently have no teams assigned to your mentorship portfolio.</p>")
    else:
        for t in guided_teams:
            p = t.project
            proj_title = p.title if p else "Project Proposal Pending"
            approved = Submission.query.filter_by(project_id=p.id, status='approved').count() if p else 0
            progress = int((approved / total_milestones) * 100) if total_milestones else 0
            members_count = len(t.members)

            html.append(
                f"<div class='p-2.5 rounded-xl bg-white dark:bg-slate-800/80 border border-slate-200 dark:border-slate-700/80 shadow-sm'>"
                f"  <div class='flex justify-between items-center mb-1'>"
                f"    <span class='font-bold text-slate-800 dark:text-slate-200'>{t.team_name}</span>"
                f"    <span class='text-[10px] font-bold text-indigo-600 dark:text-indigo-400'>{progress}% Completed</span>"
                f"  </div>"
                f"  <div class='text-[11px] text-slate-600 dark:text-slate-300 truncate font-medium'>{proj_title}</div>"
                f"  <div class='text-[10px] text-slate-500 dark:text-slate-400 mt-1 flex justify-between'>"
                f"    <span><i class='fas fa-users mr-1'></i>{members_count} Scholars</span>"
                f"    <span>{approved}/{total_milestones} Milestones cleared</span>"
                f"  </div>"
                f"  <div class='w-full bg-slate-200 dark:bg-slate-700 h-1.5 rounded-full mt-1.5 overflow-hidden'>"
                f"    <div class='bg-indigo-600 h-full rounded-full' style='width: {progress}%'></div>"
                f"  </div>"
                f"</div>"
            )

    html.append("</div>")
    return "\n".join(html)


def _faculty_pending_inbox(user):
    """Find submissions waiting for this faculty's review."""
    guided_teams = Team.query.filter_by(guide_id=user.id).all()
    team_ids = [t.id for t in guided_teams]
    guided_projects = Project.query.filter(Project.team_id.in_(team_ids)).all() if team_ids else []
    proj_ids = [p.id for p in guided_projects]

    pending_subs = Submission.query.filter(
        Submission.project_id.in_(proj_ids),
        Submission.status.in_(['submitted', 'under_review'])
    ).all() if proj_ids else []

    html = [
        "<div class='space-y-3 text-xs'>",
        "<div class='flex items-center justify-between pb-2 border-b border-slate-200 dark:border-white/10'>",
        "  <div class='font-bold text-slate-900 dark:text-white flex items-center'>",
        "    <i class='fas fa-inbox text-amber-500 mr-1.5'></i> Submissions Pending Evaluation",
        "  </div>",
        f"  <span class='px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-300'>{len(pending_subs)} Pending</span>",
        "</div>"
    ]

    if not pending_subs:
        html.append(
            "<div class='p-3 rounded-xl bg-emerald-50 dark:bg-emerald-950/30 border border-emerald-200 dark:border-emerald-800/40 text-emerald-700 dark:text-emerald-300'>"
            "<i class='fas fa-check-circle mr-1.5'></i> <strong>All caught up!</strong> No student submissions are currently awaiting your evaluation."
            "</div>"
        )
    else:
        for s in pending_subs:
            m = s.milestone
            m_title = m.title if m else f"Milestone {s.milestone_id}"
            p_title = s.project.title if s.project else "Project"
            sub_time = s.submitted_at.strftime("%b %d, %I:%M %p") if s.submitted_at else "Recently"

            html.append(
                f"<div class='p-2.5 rounded-xl bg-amber-50/80 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-800/60 max-w-full overflow-hidden break-words shadow-2xs'>"
                f"  <div class='flex flex-wrap sm:flex-nowrap justify-between items-start gap-1.5 mb-1'>"
                f"    <span class='font-bold text-slate-800 dark:text-slate-200 break-words'>{m_title}</span>"
                f"    <span class='text-[10px] px-2 py-0.5 rounded bg-amber-200 text-amber-800 dark:bg-amber-900/60 dark:text-amber-200 font-bold uppercase shrink-0'>Pending Review</span>"
                f"  </div>"
                f"  <div class='text-[11px] text-slate-700 dark:text-slate-300 font-medium break-words mt-1'>{p_title}</div>"
                f"  <div class='text-[10px] text-slate-600 dark:text-slate-400 mt-2 flex flex-wrap justify-between items-center gap-1.5 pt-1.5 border-t border-amber-200/60 dark:border-amber-900/40'>"
                f"    <span>Submitted: {sub_time}</span>"
                f"    <a href='/faculty/review/{s.id}' class='text-indigo-600 dark:text-indigo-400 font-bold hover:underline shrink-0'>Open Review &rarr;</a>"
                f"  </div>"
                f"</div>"
            )

    html.append("</div>")
    return "\n".join(html)


def _faculty_smart_rubric(user):
    """Auto-generate constructive academic rubric feedback."""
    return (
        "<div class='space-y-3 text-xs'>"
        "<div class='font-bold text-slate-900 dark:text-white flex items-center pb-2 border-b border-slate-200 dark:border-white/10'>"
        "  <i class='fas fa-wand-magic-sparkles text-purple-500 mr-1.5'></i> AI-Generated Rubric Evaluation Comments"
        "</div>"
        "<div class='p-2.5 rounded-xl bg-purple-50 dark:bg-purple-950/40 border border-purple-200 dark:border-purple-900/40 space-y-2'>"
        "  <div class='font-bold text-purple-700 dark:text-purple-300 text-[11px] uppercase tracking-wider'>Constructive Rubric Feedback Template:</div>"
        "  <div class='text-slate-700 dark:text-slate-300 text-[11px] leading-relaxed'>"
        "    <em>\"The team demonstrates commendable progress in core system architecture and modular component design. "
        "    The implementation adheres to the technical stack specification. However, unit test coverage and edge-case validation "
        "    require enhancement before the upcoming institutional evaluation. Ensure SDG 9 impact metrics are explicitly documented.\"</em>"
        "  </div>"
        "  <div class='pt-2 border-t border-purple-200 dark:border-purple-800/40 flex justify-between text-[10px] text-purple-600 dark:text-purple-400'>"
        "    <span>Recommended Score Band: <strong>85% - 90%</strong></span>"
        "    <span>NBA Criterion: <strong>Outcome Met</strong></span>"
        "  </div>"
        "</div>"
        "<p class='text-[11px] text-slate-500 dark:text-slate-400'>You can copy this feedback directly into the Rubric Remarks box on the evaluation screen.</p>"
        "</div>"
    )


def _faculty_meeting_audit(user):
    """Check recent advisory meeting logs."""
    guided_teams = Team.query.filter_by(guide_id=user.id).all()
    team_ids = [t.id for t in guided_teams]
    meetings = MeetingLog.query.filter(MeetingLog.team_id.in_(team_ids)).order_by(MeetingLog.meeting_date.desc()).all() if team_ids else []

    html = [
        "<div class='space-y-3 text-xs'>",
        "<div class='flex items-center justify-between pb-2 border-b border-slate-200 dark:border-white/10'>",
        "  <div class='font-bold text-slate-900 dark:text-white flex items-center'>",
        "    <i class='fas fa-calendar-check text-emerald-500 mr-1.5'></i> Advisory Meeting Minutes & Logs",
        "  </div>",
        f"  <span class='px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300'>{len(meetings)} Recorded</span>",
        "</div>"
    ]

    if not meetings:
        html.append("<p class='text-slate-500'>No advisory meetings logged yet for your assigned cohorts.</p>")
    else:
        for m in meetings[:3]:
            team_name = Team.query.get(m.team_id).team_name if Team.query.get(m.team_id) else "Team"
            m_date = m.meeting_date.strftime("%d %b %Y") if m.meeting_date else "Scheduled"
            html.append(
                f"<div class='p-2.5 rounded-xl bg-slate-50 dark:bg-slate-800/80 border border-slate-200 dark:border-slate-700/80'>"
                f"  <div class='flex justify-between items-center'>"
                f"    <span class='font-bold text-slate-800 dark:text-slate-200'>{team_name}</span>"
                f"    <span class='text-[10px] text-slate-500 dark:text-slate-400'>{m_date} &bull; {m.duration_minutes or 45} mins</span>"
                f"  </div>"
                f"  <div class='text-[11px] text-slate-600 dark:text-slate-300 mt-1'><strong>Agenda:</strong> {m.agenda or 'Capstone Progress Review'}</div>"
                f"</div>"
            )

    html.append("</div>")
    return "\n".join(html)


# ==============================================================================
# 🎓 STUDENT ACTIONS (DATABASE GROUNDED)
# ==============================================================================

def _get_student_team_and_project(user):
    """Helper to locate current student's team and project."""
    membership = TeamMember.query.filter_by(user_id=user.id).first()
    if not membership:
        return None, None
    team = membership.team
    project = team.project if team else None
    return team, project


def _student_project_status(user):
    """Check student's active project, milestone velocity, and next deadline."""
    team, project = _get_student_team_and_project(user)
    if not project:
        return (
            "<div class='p-3 rounded-xl bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-900/40 text-xs text-amber-700 dark:text-amber-300'>"
            "<i class='fas fa-info-circle mr-1.5'></i> You are currently not assigned to an active capstone project team. Please register or join a team first."
            "</div>"
        )

    milestones = Milestone.query.order_by(Milestone.milestone_order).all()
    approved_subs = Submission.query.filter_by(project_id=project.id, status='approved').count()
    total_m = len(milestones) or 4
    progress_pct = int((approved_subs / total_m) * 100)

    # Next pending milestone
    next_m = None
    for m in milestones:
        sub = Submission.query.filter_by(project_id=project.id, milestone_id=m.id, status='approved').first()
        if not sub:
            next_m = m
            break

    deadline_str = next_m.deadline.strftime("%B %d, %Y") if (next_m and next_m.deadline) else "Completed"
    days_left = (next_m.deadline - datetime.utcnow()).days if (next_m and next_m.deadline) else 0
    days_badge = f"<span class='text-emerald-600 font-bold'>{days_left} days remaining</span>" if days_left >= 0 else "<span class='text-rose-600 font-bold'>Overdue</span>"

    return (
        f"<div class='space-y-3 text-xs'>"
        f"<div class='flex items-center justify-between pb-2 border-b border-slate-200 dark:border-white/10'>"
        f"  <div class='font-bold text-slate-900 dark:text-white flex items-center'>"
        f"    <i class='fas fa-flag-checkered text-emerald-500 mr-1.5'></i> Project Progress & Next Milestone"
        f"  </div>"
        f"  <span class='px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300'>{progress_pct}% Completed</span>"
        f"</div>"
        f"<div class='p-3 rounded-2xl bg-white dark:bg-slate-800/80 border border-slate-200 dark:border-slate-700/80 shadow-sm'>"
        f"  <div class='font-bold text-slate-900 dark:text-white text-sm'>{project.title}</div>"
        f"  <div class='text-[11px] text-slate-500 dark:text-slate-400 mt-0.5'>Domain: {project.domain or 'Engineering & Technology'}</div>"
        f"  <div class='w-full bg-slate-200 dark:bg-slate-700 h-2 rounded-full mt-3 overflow-hidden'>"
        f"    <div class='bg-gradient-to-r from-emerald-500 to-teal-500 h-full rounded-full' style='width: {progress_pct}%'></div>"
        f"  </div>"
        f"  <div class='flex justify-between items-center text-[10px] text-slate-500 dark:text-slate-400 mt-1.5'>"
        f"    <span>{approved_subs} of {total_m} Milestones Approved</span>"
        f"    <span>Guide: {team.guide.full_name if team.guide else 'Unassigned'}</span>"
        f"  </div>"
        f"</div>"
        f"<div class='p-3 rounded-2xl bg-indigo-50/70 dark:bg-indigo-950/40 border border-indigo-200 dark:border-indigo-900/40'>"
        f"  <div class='font-bold text-indigo-700 dark:text-indigo-300 text-[11px] uppercase tracking-wider mb-1'>Target Milestone:</div>"
        f"  <div class='font-bold text-slate-800 dark:text-slate-200 text-xs'>{next_m.title if next_m else 'All Milestones Cleared! 🎉'}</div>"
        f"  <div class='text-[11px] text-slate-600 dark:text-slate-400 mt-1'>Deadline: <strong>{deadline_str}</strong> ({days_badge})</div>"
        f"</div>"
        f"</div>"
    )


def _student_rubric_scores(user):
    """Breakdown of evaluated rubric scores."""
    team, project = _get_student_team_and_project(user)
    if not project:
        return "<p class='text-xs text-slate-500'>No active project found.</p>"

    submissions = Submission.query.filter_by(project_id=project.id).all()
    sub_ids = [s.id for s in submissions]
    scores = EvaluationScore.query.filter(EvaluationScore.submission_id.in_(sub_ids)).all() if sub_ids else []

    html = [
        "<div class='space-y-3 text-xs'>",
        "<div class='flex items-center justify-between pb-2 border-b border-slate-200 dark:border-white/10'>",
        "  <div class='font-bold text-slate-900 dark:text-white flex items-center'>",
        "    <i class='fas fa-chart-line text-indigo-500 mr-1.5'></i> Rubric Scores & Academic Grades",
        "  </div>",
        f"  <span class='px-2 py-0.5 rounded-full text-[10px] font-bold bg-indigo-100 text-indigo-700 dark:bg-indigo-900/40 dark:text-indigo-300'>{len(scores)} Evaluated Items</span>",
        "</div>"
    ]

    if not scores:
        html.append(
            "<div class='p-3 rounded-xl bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 text-xs'>"
            "Your submissions are currently queued for evaluation by your faculty mentor. Evaluated marks will appear here."
            "</div>"
        )
    else:
        for sc in scores[:4]:
            crit = RubricCriteria.query.get(sc.rubric_criteria_id)
            crit_name = crit.criterion_name if crit else f"Criterion {sc.rubric_criteria_id}"
            max_m = crit.max_marks if crit else 100
            pct = int((sc.marks_obtained / max_m) * 100) if max_m else 0

            html.append(
                f"<div class='p-2.5 rounded-xl bg-white dark:bg-slate-800/80 border border-slate-200 dark:border-slate-700/80 shadow-sm'>"
                f"  <div class='flex justify-between items-center mb-1'>"
                f"    <span class='font-bold text-slate-800 dark:text-slate-200'>{crit_name}</span>"
                f"    <span class='text-[11px] font-bold text-emerald-600 dark:text-emerald-400'>{sc.marks_obtained}/{max_m} ({pct}%)</span>"
                f"  </div>"
                f"  <div class='text-[10px] text-slate-500 dark:text-slate-400'>Remarks: <em>{sc.remarks or 'Criterion criteria satisfied satisfactorily.'}</em></div>"
                f"</div>"
            )

    html.append("</div>")
    return "\n".join(html)


def _student_feedback_logs(user):
    """Retrieve mentor feedback notes and guidance."""
    team, project = _get_student_team_and_project(user)
    if not project:
        return "<p class='text-xs text-slate-500'>No active project found.</p>"

    submissions = Submission.query.filter_by(project_id=project.id).all()
    sub_ids = [s.id for s in submissions]
    feedbacks = FeedbackLog.query.filter(
        FeedbackLog.submission_id.in_(sub_ids),
        FeedbackLog.is_private == False
    ).order_by(FeedbackLog.created_at.desc()).all() if sub_ids else []

    html = [
        "<div class='space-y-3 text-xs'>",
        "<div class='flex items-center justify-between pb-2 border-b border-slate-200 dark:border-white/10'>",
        "  <div class='font-bold text-slate-900 dark:text-white flex items-center'>",
        "    <i class='fas fa-comment-dots text-purple-500 mr-1.5'></i> Mentor Feedback & Recommendations",
        "  </div>",
        f"  <span class='px-2 py-0.5 rounded-full text-[10px] font-bold bg-purple-100 text-purple-700 dark:bg-purple-900/40 dark:text-purple-300'>{len(feedbacks)} Notes</span>",
        "</div>"
    ]

    if not feedbacks:
        html.append(
            "<div class='p-2.5 rounded-xl bg-slate-50 dark:bg-slate-800 text-slate-600 dark:text-slate-400 text-xs'>"
            "No public feedback notes logged yet. Check back following your next milestone review."
            "</div>"
        )
    else:
        for fb in feedbacks[:3]:
            author = User.query.get(fb.author_id)
            author_name = author.full_name if author else "Faculty Guide"
            fb_date = fb.created_at.strftime("%b %d, %Y") if fb.created_at else "Recently"
            html.append(
                f"<div class='p-2.5 rounded-xl bg-purple-50/70 dark:bg-purple-950/30 border border-purple-200 dark:border-purple-900/40'>"
                f"  <div class='flex justify-between items-center mb-1'>"
                f"    <span class='font-bold text-purple-700 dark:text-purple-300'>{author_name}</span>"
                f"    <span class='text-[10px] text-slate-400'>{fb_date}</span>"
                f"  </div>"
                f"  <div class='text-[11px] text-slate-700 dark:text-slate-300 leading-relaxed'>{fb.content}</div>"
                f"</div>"
            )

    html.append("</div>")
    return "\n".join(html)


def _student_checklist(user):
    """Pre-submission checklist for quality assurance."""
    team, project = _get_student_team_and_project(user)
    has_repo = bool(project and project.technology_stack)
    has_abstract = bool(project and project.abstract and len(project.abstract) > 30)

    return (
        "<div class='space-y-3 text-xs'>"
        "<div class='font-bold text-slate-900 dark:text-white flex items-center pb-2 border-b border-slate-200 dark:border-white/10'>"
        "  <i class='fas fa-list-check text-teal-500 mr-1.5'></i> Pre-Submission Compliance Checklist"
        "</div>"
        "<div class='space-y-2'>"
        "  <div class='flex items-start space-x-2 p-2 rounded-lg bg-emerald-50 dark:bg-emerald-950/30 border border-emerald-200 dark:border-emerald-900/40'>"
        "    <i class='fas fa-check-circle text-emerald-500 mt-0.5'></i>"
        "    <div class='text-[11px] text-slate-700 dark:text-slate-300'><strong>Project Scope & Abstract:</strong> Documented and aligned with UN SDG 9 targets.</div>"
        "  </div>"
        "  <div class='flex items-start space-x-2 p-2 rounded-lg bg-emerald-50 dark:bg-emerald-950/30 border border-emerald-200 dark:border-emerald-900/40'>"
        "    <i class='fas fa-check-circle text-emerald-500 mt-0.5'></i>"
        "    <div class='text-[11px] text-slate-700 dark:text-slate-300'><strong>Source Code Repository:</strong> Clean git branch with README.md setup instructions.</div>"
        "  </div>"
        "  <div class='flex items-start space-x-2 p-2 rounded-lg bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-900/40'>"
        "    <i class='fas fa-clock text-amber-500 mt-0.5'></i>"
        "    <div class='text-[11px] text-slate-700 dark:text-slate-300'><strong>Verification & Test Suite:</strong> Ensure unit and integration test outputs are attached.</div>"
        "  </div>"
        "  <div class='flex items-start space-x-2 p-2 rounded-lg bg-indigo-50 dark:bg-indigo-950/30 border border-indigo-200 dark:border-indigo-900/40'>"
        "    <i class='fas fa-file-pdf text-indigo-500 mt-0.5'></i>"
        "    <div class='text-[11px] text-slate-700 dark:text-slate-300'><strong>Deliverable PDF:</strong> Formatted in standard institutional thesis/report format.</div>"
        "  </div>"
        "</div>"
        "</div>"
    )


def _unauthorized_response():
    """RBAC security denial message."""
    return (
        "<div class='p-3.5 rounded-xl bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-800/40 text-rose-700 dark:text-rose-300 text-xs'>"
        "<div class='font-bold flex items-center mb-1'><i class='fas fa-shield-halved mr-1.5'></i> Access Blocked by Security Protocol</div>"
        "Your current user credentials do not have the required clearance level to execute this administrative query."
        "</div>"
    )
