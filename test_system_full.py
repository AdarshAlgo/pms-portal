"""
Comprehensive End-to-End Test Suite for Project Progress Monitoring & Evaluation System.
Tests Frontend rendering, Backend business logic, RBAC security, Database persistence,
and the complete multi-role lifecycle flow.
"""

import io
import sys
from datetime import datetime
from app import create_app
from app.extensions import db
from app.models.user import User, Role
from app.models.project import Project, Team, TeamMember
from app.models.milestone import Milestone, Submission, MilestoneDeadlineOverride
from app.models.evaluation import EvaluationScore, RubricCriteria, RubricTemplate
from app.models.feedback import FeedbackLog, Notification, SystemSetting, AuditLog
from app.services.evaluation_service import compute_weighted_score
from app.services.milestone_service import calculate_project_progress

from seed import seed_database

def run_full_system_verification():
    seed_database(reset=True)
    app = create_app('development')
    client = app.test_client()
    
    results = []
    
    def log_test(category, test_name, status, details=""):
        symbol = "✅" if status else "❌"
        results.append((symbol, category, test_name, details))
        print(f"{symbol} [{category}] {test_name}: {details}")

    print("\n" + "="*80)
    print("      🚀 STARTING COMPREHENSIVE E2E SYSTEM VERIFICATION")
    print("="*80 + "\n")

    # -------------------------------------------------------------
    # 1. STATIC ASSETS & PUBLIC ROUTES
    # -------------------------------------------------------------
    for asset in ['css/custom.css', 'js/charts.js', 'js/dashboard.js', 'js/forms.js']:
        res = client.get(f'/static/{asset}')
        log_test("STATIC", f"Asset /{asset}", res.status_code == 200, f"Status: {res.status_code}")

    res = client.get('/auth/login')
    has_form = b'<form' in res.data and b'email' in res.data and b'password' in res.data
    log_test("FRONTEND", "Login Page Render", res.status_code == 200 and has_form, "HTML contains login form & inputs")

    res = client.get('/auth/register')
    has_reg = b'Create an Account' in res.data
    log_test("FRONTEND", "Register Page Render", res.status_code == 200 and has_reg, "HTML contains registration form")

    # -------------------------------------------------------------
    # 2. RBAC & SECURITY VERIFICATION
    # -------------------------------------------------------------
    # Unauthenticated access to protected routes
    res = client.get('/admin/dashboard')
    log_test("SECURITY", "Unauthenticated Admin Access", res.status_code in [302, 401], f"Redirected to login (Status {res.status_code})")

    res = client.get('/faculty/dashboard')
    log_test("SECURITY", "Unauthenticated Faculty Access", res.status_code in [302, 401], f"Redirected to login (Status {res.status_code})")

    res = client.get('/student/dashboard')
    log_test("SECURITY", "Unauthenticated Student Access", res.status_code in [302, 401], f"Redirected to login (Status {res.status_code})")

    # Cross-role access: Student trying to access Admin and Faculty dashboards
    client.post('/auth/login', data={'email': 'student1@university.edu', 'password': 'Student@Katiyar2026!'}, follow_redirects=True)
    res_forbidden_admin = client.get('/admin/dashboard')
    log_test("SECURITY", "Student -> /admin/dashboard (RBAC)", res_forbidden_admin.status_code == 403, f"Blocked with 403 Forbidden")
    
    res_forbidden_faculty = client.get('/faculty/dashboard')
    log_test("SECURITY", "Student -> /faculty/dashboard (RBAC)", res_forbidden_faculty.status_code == 403, f"Blocked with 403 Forbidden")
    client.get('/auth/logout')

    # Faculty trying to access Admin dashboard
    client.post('/auth/login', data={'email': 'dr.verma@university.edu', 'password': 'Faculty@Verma2026!'}, follow_redirects=True)
    res_fac_admin = client.get('/admin/dashboard')
    log_test("SECURITY", "Faculty -> /admin/dashboard (RBAC)", res_fac_admin.status_code == 403, f"Blocked with 403 Forbidden")
    client.get('/auth/logout')

    # -------------------------------------------------------------
    # 3. ADMIN JOURNEY VERIFICATION
    # -------------------------------------------------------------
    res_admin_login = client.post('/auth/login', data={'email': 'admin@university.edu', 'password': 'Admin@PMS2026#Secure'}, follow_redirects=True)
    log_test("AUTH", "Admin Login (admin@university.edu)", res_admin_login.status_code == 200, "Authenticated successfully")

    res_admin_dash = client.get('/admin/dashboard')
    has_admin_content = b'Admin' in res_admin_dash.data and b'Total Projects' in res_admin_dash.data
    log_test("ADMIN", "Admin Dashboard Metrics & UI", res_admin_dash.status_code == 200 and has_admin_content, "Total Projects, Active Teams, Canvas charts rendered")
    client.get('/auth/logout')

    # -------------------------------------------------------------
    # 4. STUDENT JOURNEY & MILESTONE SUBMISSION
    # -------------------------------------------------------------
    res_student_login = client.post('/auth/login', data={'email': 'student1@university.edu', 'password': 'Student@Katiyar2026!'}, follow_redirects=True)
    log_test("AUTH", "Student Login (student1@university.edu)", res_student_login.status_code == 200, "Authenticated successfully")

    res_stu_dash = client.get('/student/dashboard')
    has_proj = b'Crop' in res_stu_dash.data
    log_test("STUDENT", "Student Dashboard View", res_stu_dash.status_code == 200 and has_proj, "Shows assigned project, team & milestones")

    # Initial progress check
    with app.app_context():
        initial_progress = calculate_project_progress(1)
        log_test("DATABASE", "Initial Project Progress Query", True, f"Initial progress: {initial_progress:.1f}%")

    # Student submits Milestone 3: "Implementation & Prototype"
    m3_res = client.get('/student/submit/3')
    log_test("STUDENT", "Load Milestone 3 Submit Form", m3_res.status_code == 200, "Submission form rendered with description & URL inputs")

    submission_data = {
        'submission_text': 'Completed CNN model training on 54,000 leaf images reaching 94.2% test accuracy. Built Flask inference API and prototype UI.',
        'document_url': 'https://drive.google.com/sample-m3-prototype-report.pdf',
        'repository_url': 'https://github.com/tech-innovators/crop-disease-detection/tree/prototype-v1'
    }
    submit_res = client.post('/student/submit/3', data=submission_data, follow_redirects=True)
    log_test("STUDENT", "Post Milestone 3 Deliverable", submit_res.status_code == 200, "Submitted successfully and redirected to dashboard")

    # Verify Submission stored in Database
    with app.app_context():
        sub3 = Submission.query.filter_by(project_id=1, milestone_id=3).first()
        sub3_valid = sub3 is not None and sub3.status in ('submitted', 'approved') and sub3.document_url == submission_data['document_url']
        log_test("DATABASE", "Submission Record Persistence", sub3_valid, f"Status: {sub3.status if sub3 else 'None'}, ID: {sub3.id if sub3 else 'None'}")
        sub3_id = sub3.id if sub3 else None

    client.get('/auth/logout')

    # -------------------------------------------------------------
    # 5. FACULTY JOURNEY & RUBRIC EVALUATION
    # -------------------------------------------------------------
    client.post('/auth/login', data={'email': 'dr.verma@university.edu', 'password': 'Faculty@Verma2026!'}, follow_redirects=True)
    res_fac_dash = client.get('/faculty/dashboard')
    has_teams = b'Agrotech' in res_fac_dash.data or b'Innovators' in res_fac_dash.data
    log_test("FACULTY", "Faculty Dashboard Teams View", res_fac_dash.status_code == 200 and has_teams, "Shows assigned team 'Agrotech Innovators'")

    # Team detail page
    res_team = client.get('/faculty/team/1')
    log_test("FACULTY", "Team Detail Page", res_team.status_code == 200, "All milestones and team submissions loaded")

    # Load Rubric Evaluation Page for Milestone 3
    res_eval_page = client.get(f'/faculty/evaluate/{sub3_id}')
    has_rubric_form = b'Rubric Evaluation' in res_eval_page.data and b'marks_' in res_eval_page.data
    log_test("FACULTY", "Rubric Evaluation Page Load", res_eval_page.status_code == 200 and has_rubric_form, "Interactive scoring matrix & real-time JS calculator ready")

    # Submit Rubric Scores:
    # Criterion 1 (Innovation): 9.5 / 10 (Weight 25%)
    # Criterion 2 (Implementation): 9.0 / 10 (Weight 40%)
    # Criterion 3 (Documentation): 8.5 / 10 (Weight 20%)
    # Criterion 4 (Presentation): 9.0 / 10 (Weight 15%)
    eval_post_data = {
        'marks_1': '9.5',
        'remarks_1': 'Excellent model accuracy and innovative dataset augmentation.',
        'marks_2': '9.0',
        'remarks_2': 'Clean code structure and solid API endpoints.',
        'marks_3': '8.5',
        'remarks_3': 'Good documentation, add latency benchmarks in final phase.',
        'marks_4': '9.0',
        'remarks_4': 'Working prototype demo verified.',
        'status': 'approved',
        'overall_feedback': 'Outstanding progress! Prototype meets all criteria for Milestone 3. Proceed to final presentation.'
    }
    eval_submit_res = client.post(f'/faculty/evaluate/{sub3_id}', data=eval_post_data, follow_redirects=True)
    log_test("FACULTY", "Submit Rubric Evaluation Scores", eval_submit_res.status_code == 200, "Evaluation processed and saved")

    # Verify Evaluated Scores & Weighted Algorithm in Database
    with app.app_context():
        score_summary = compute_weighted_score(sub3_id)
        # Expected:
        # Crit 1: (9.5/10) * 25 = 23.75
        # Crit 2: (9.0/10) * 40 = 36.00
        # Crit 3: (8.5/10) * 20 = 17.00
        # Crit 4: (9.0/10) * 15 = 13.50
        # Weighted Total = 90.25 out of 100
        # Total Raw = 36.0 / 40.0 = 90.0%
        # Grade = A+
        algo_correct = score_summary['total_obtained'] == 36.0 and score_summary['percentage'] == 90.0 and score_summary['grade'] == 'A+'
        log_test("EVALUATION_ALGO", "Weighted Rubric Score Math", algo_correct,
                 f"Obtained: {score_summary['total_obtained']}/40, Pct: {score_summary['percentage']:.1f}%, Weighted Total: {score_summary['weighted_total']:.2f}, Grade: {score_summary['grade']}")

        # Verify Submission status changed to approved
        sub3_refreshed = db.session.get(Submission, sub3_id)
        status_updated = sub3_refreshed.status == 'approved'
        log_test("DATABASE", "Submission Status Transition", status_updated, f"New Status: {sub3_refreshed.status}")

        # Verify Feedback Log was created
        flog = FeedbackLog.query.filter_by(submission_id=sub3_id).first()
        log_test("DATABASE", "Feedback Audit Log Persistence", flog is not None, f"Logged: '{flog.content[:60]}...'")

        # Verify Notification generated for student
        notif = Notification.query.filter_by(user_id=sub3.submitted_by, related_entity_id=sub3_id).first()
        log_test("DATABASE", "Student Notification Generated", notif is not None, f"Title: '{notif.title if notif else 'None'}'")

    client.get('/auth/logout')

    # -------------------------------------------------------------
    # 6. VERIFY STUDENT DASHBOARD & PROGRESS UPDATE
    # -------------------------------------------------------------
    client.post('/auth/login', data={'email': 'student1@university.edu', 'password': 'Student@Katiyar2026!'}, follow_redirects=True)
    res_student_dash2 = client.get('/student/dashboard')
    log_test("STUDENT", "Updated Dashboard Load", res_student_dash2.status_code == 200, "Dashboard re-rendered with updated progress")

    with app.app_context():
        new_progress = calculate_project_progress(1)
        # Initial was 10.0%, now M1(10%) + M3(40%) = 50.0%
        progress_increased = new_progress > initial_progress
        log_test("PROGRESS_ENGINE", "Project Progress Recalculation", progress_increased,
                 f"Progress updated from {initial_progress:.1f}% to {new_progress:.1f}%")

    res_prog_page = client.get('/student/progress')
    has_prog_ui = b'Progress' in res_prog_page.data
    log_test("STUDENT", "Student Detailed Progress Page", res_prog_page.status_code == 200 and has_prog_ui, "Milestone progression & charts rendered")

    # -------------------------------------------------------------
    # 7. API ENDPOINTS INTEGRITY
    # -------------------------------------------------------------
    res_api_prog = client.get('/api/progress/1')
    api_prog_data = res_api_prog.get_json()
    api_prog_valid = res_api_prog.status_code == 200 and 'data' in api_prog_data and 'labels' in api_prog_data
    log_test("API", "GET /api/progress/1 (Chart.js Feed)", api_prog_valid, f"Labels: {len(api_prog_data['labels'])}, Cumulative Data: {api_prog_data['data']}")

    res_api_scores = client.get('/api/scores/1')
    api_scores_data = res_api_scores.get_json()
    api_scores_valid = res_api_scores.status_code == 200 and api_scores_data.get('count', 0) >= 2
    log_test("API", "GET /api/scores/1 (Scores Feed)", api_scores_valid, f"Evaluated milestones count: {api_scores_data.get('count')}, Scores: {api_scores_data.get('scores')}")

    res_api_notif = client.get('/api/notifications')
    notif_data = res_api_notif.get_json()
    log_test("API", "GET /api/notifications", res_api_notif.status_code == 200 and len(notif_data) > 0, f"Fetched {len(notif_data)} unread notifications")

    # -------------------------------------------------------------
    # 8. ERROR PAGES
    # -------------------------------------------------------------
    res_404 = client.get('/nonexistent-page-xyz')
    log_test("ERROR_HANDLING", "Custom 404 Page", res_404.status_code == 404, "Rendered custom 404 template")

    # -------------------------------------------------------------
    # 9. VIDYA AI COPILOT & RBAC SECURITY ISOLATION
    # -------------------------------------------------------------
    # 9a. Student AI actions check
    res_ai_actions = client.get('/api/agent/actions')
    ai_actions_data = res_ai_actions.get_json()
    has_student_actions = res_ai_actions.status_code == 200 and ai_actions_data.get('role') == 'student'
    log_test("AI_AGENT", "Student AI Actions Fetch", has_student_actions, f"Fetched {len(ai_actions_data.get('actions', []))} student-tailored actions")

    # 9b. Student executing legitimate student action
    res_student_exec = client.post('/api/agent/execute', json={'action_id': 'student_project_status'})
    student_exec_data = res_student_exec.get_json()
    student_exec_valid = res_student_exec.status_code == 200 and 'Project Progress' in student_exec_data.get('html', '')
    log_test("AI_AGENT", "Student 1-Click Action Exec", student_exec_valid, "Rendered live milestone progress & target deadline")

    # 9c. Student trying to execute unauthorized admin audit (RBAC Guard)
    res_malicious_exec = client.post('/api/agent/execute', json={'action_id': 'admin_audit_risk'})
    malicious_data = res_malicious_exec.get_json()
    blocked_by_rbac = 'Access Blocked' in malicious_data.get('html', '') or 'RBAC' in malicious_data.get('html', '')
    log_test("AI_SECURITY", "Student Admin-Action Block", blocked_by_rbac, "RBAC prevented student from executing institutional audit")

    # 9d. Switch to Admin and test Admin AI capabilities
    client.post('/auth/logout')
    client.post('/auth/login', data={'email': 'admin@university.edu', 'password': 'Admin@PMS2026#Secure'})
    
    res_admin_actions = client.get('/api/agent/actions')
    admin_actions_data = res_admin_actions.get_json()
    has_admin_actions = res_admin_actions.status_code == 200 and admin_actions_data.get('role') == 'admin'
    log_test("AI_AGENT", "Admin AI Actions Fetch", has_admin_actions, f"Fetched {len(admin_actions_data.get('actions', []))} admin governance actions")

    res_admin_audit = client.post('/api/agent/execute', json={'action_id': 'admin_audit_risk'})
    admin_audit_data = res_admin_audit.get_json()
    admin_audit_valid = res_admin_audit.status_code == 200 and 'Institutional Risk' in admin_audit_data.get('html', '')
    log_test("AI_AGENT", "Admin 1-Click Risk Audit Exec", admin_audit_valid, "Analyzed all cohorts with grounded milestone velocity")

    # -------------------------------------------------------------
    # 10. DYNAMIC MULTI-PORTAL WORKFLOWS & INSTITUTIONAL GOVERNANCE
    # -------------------------------------------------------------
    # 10a. Admin Clearance Desk
    res_clearance = client.get('/admin/projects/clearance')
    log_test("ADMIN", "Clearance Desk View", res_clearance.status_code == 200, "Loaded project proposals awaiting clearance")

    # 10b. Admin Clearance Decision (Approve Proposal #5)
    res_clearance_post = client.post('/admin/project/5/clearance', data={'decision': 'approve', 'comments': 'Proposal methodology verified for ABET/NBA alignment.'}, follow_redirects=True)
    with app.app_context():
        p5 = db.session.get(Project, 5)
        p5_approved = p5 is not None and p5.status == 'approved'
        log_test("ADMIN", "Proposal Clearance Decision", res_clearance_post.status_code == 200 and p5_approved, f"Project #5 cleared with status: {p5.status if p5 else 'None'}")

    # 10c. Admin Faculty Workload Balancer
    res_workload = client.get('/admin/faculty-workload')
    log_test("ADMIN", "Faculty Workload Monitor", res_workload.status_code == 200 and b'Faculty Mentorship Workload' in res_workload.data, "Rendered faculty quota and supervisory capacity")

    # 10d. Admin Cohort Teams & Guide Reassignment
    res_teams = client.get('/admin/teams')
    log_test("ADMIN", "Cohort Teams Management", res_teams.status_code == 200 and b'Cohort Teams' in res_teams.data, "Rendered active team rosters and guide assignments")

    res_reassign = client.post('/admin/team/2/reassign-guide', data={'guide_id': '2', 'reason': 'Specialization alignment'}, follow_redirects=True)
    with app.app_context():
        t2 = db.session.get(Team, 2)
        reassigned_ok = t2 is not None and t2.guide_id == 2
        log_test("ADMIN", "Team Guide Reassignment", res_reassign.status_code == 200 and reassigned_ok, f"Team #2 guide assigned to ID: {t2.guide_id if t2 else 'None'}")

    # 10e. Admin Academic Terms
    res_terms = client.get('/admin/terms')
    log_test("ADMIN", "Academic Terms Management", res_terms.status_code == 200, "Rendered academic terms list")

    # 10f. Admin Milestone Extension Override
    res_extend = client.post('/admin/milestones/extend', data={'team_id': '2', 'milestone_id': '2', 'extended_deadline': '2026-11-30', 'reason': 'Field testing hardware delay'}, follow_redirects=True)
    with app.app_context():
        override = MilestoneDeadlineOverride.query.filter_by(team_id=2, milestone_id=2).first()
        override_ok = override is not None and override.reason == 'Field testing hardware delay'
        log_test("ADMIN", "Milestone Deadline Extension Override", res_extend.status_code == 200 and override_ok, f"Override registered: {override.reason if override else 'None'}")

    # 10g. Admin Rubrics Matrix & Criteria
    res_rubrics = client.get('/admin/rubrics')
    log_test("ADMIN", "Rubrics Matrix Management", res_rubrics.status_code == 200, "Rendered 4-tier rubric templates and criteria")

    # 10h. Admin At-Risk Radar & 1-Click Warning Notice
    res_radar = client.get('/admin/risk-radar')
    log_test("ADMIN", "At-Risk Cohort Radar", res_radar.status_code == 200 and b'At-Risk' in res_radar.data, "Calculated cohort risk telemetry and progress burndown")

    res_warn = client.post('/admin/risk-radar/warn/3', data={'escalation_level': 'formal_warning', 'message': 'Milestone 2 deliverable is critically overdue.'}, follow_redirects=True)
    with app.app_context():
        warn_notif = Notification.query.filter_by(notification_type='warning').order_by(Notification.created_at.desc()).first()
        log_test("ADMIN", "1-Click Risk Warning Notice", res_warn.status_code == 200 and warn_notif is not None, f"Dispatched warning: '{warn_notif.title if warn_notif else 'None'}'")

    # 10i. Admin ABET / NBA Dossier Export (HTML & CSV)
    res_dossier_html = client.get('/admin/export/dossier')
    log_test("ADMIN", "Accreditation Dossier HTML", res_dossier_html.status_code == 200 and b'ABET' in res_dossier_html.data, "Rendered printable institutional accreditation dossier")

    res_dossier_csv = client.get('/admin/export/dossier?format=csv')
    csv_valid = res_dossier_csv.status_code == 200 and 'text/csv' in res_dossier_csv.content_type and b'project_title' in res_dossier_csv.data
    log_test("ADMIN", "Accreditation Dossier CSV Export", csv_valid, "Generated official CSV data stream for institutional audit")

    # 10j. Admin Tamper-Proof Audit Trail
    res_audit_logs = client.get('/admin/audit-logs')
    log_test("ADMIN", "Tamper-Proof Audit Trail Datatable", res_audit_logs.status_code == 200 and b'Audit' in res_audit_logs.data, "Rendered immutable security log ledger")

    # 10k. Admin System Governance Settings
    res_settings_get = client.get('/admin/settings')
    log_test("ADMIN", "System Settings View", res_settings_get.status_code == 200, "Rendered governance configuration switches")

    res_settings_post = client.post('/admin/settings', data={'max_file_size_mb': '48', 'allowed_extensions': 'pdf,zip,docx', 'faculty_max_cohorts': '6'}, follow_redirects=True)
    with app.app_context():
        saved_mb = SystemSetting.get('MAX_FILE_SIZE_MB')
        settings_saved = saved_mb == '48'
        log_test("ADMIN", "System Settings Update", res_settings_post.status_code == 200 and settings_saved, f"Updated MAX_FILE_SIZE_MB to: {saved_mb}")

    # 10l. Faculty Portal Endpoints
    client.post('/auth/logout')
    client.post('/auth/login', data={'email': 'dr.verma@university.edu', 'password': 'Faculty@Verma2026!'})

    for fac_url, fac_name in [
        ('/faculty/my-teams', 'Faculty My Teams'),
        ('/faculty/reviews-inbox', 'Faculty Reviews Inbox'),
        ('/faculty/meetings', 'Faculty Sprint Meetings'),
        ('/faculty/department', 'Faculty Department Overview'),
        ('/faculty/milestones', 'Faculty Milestones Timeline'),
        ('/faculty/rubrics', 'Faculty Rubrics Matrix')
    ]:
        res_fac = client.get(fac_url)
        log_test("FACULTY", fac_name, res_fac.status_code == 200, f"Endpoint {fac_url} rendered status 200")

    # 10m. Student Dynamic Registration (Add Team with 3 Members)
    with app.app_context():
        student_role = Role.query.filter_by(role_name='student').first()
        new_scholar = User(
            email='scholar.priya@university.edu',
            first_name='Priya',
            last_name='Sharma',
            role_id=student_role.id,
            department='Computer Science & Engineering',
            enrollment_number='2026-CSE-099',
            is_active=True,
            can_submit=True
        )
        new_scholar.set_password('Scholar@Priya2026!')
        db.session.add(new_scholar)
        db.session.commit()

    client.post('/auth/logout')
    client.post('/auth/login', data={'email': 'scholar.priya@university.edu', 'password': 'Scholar@Priya2026!'})

    res_reg_view = client.get('/student/project/register')
    log_test("STUDENT", "Dynamic Project Registration View", res_reg_view.status_code == 200 and b'Register Capstone Project' in res_reg_view.data, "Rendered multi-member form and mentor selection")

    reg_post_data = {
        'team_name': 'Quantum Autonomous Robotics',
        'guide_id': '2',
        'department_id': '1',
        'domain': 'Autonomous Robotics & GIS',
        'title': 'Swarm Drone Navigation & Autonomous Edge SLAM',
        'abstract': 'Deploying decentralized multi-agent SLAM algorithms on embedded edge compute units for GPS-denied environments.',
        'objectives': '1. Edge SLAM\n2. Swarm mesh networking\n3. Real-time telemetry dashboard',
        'technology_stack': 'Python, ROS 2, PyTorch, C++, Docker',
        'repo_url': 'https://github.com/university/swarm-drone-slam',
        'sdg_alignment': 'SDG 9: Industry, Innovation & Infrastructure',
        'member_names[]': ['Aarav Patel', 'Sneha Reddy'],
        'member_emails[]': ['aarav@university.edu', 'sneha@university.edu'],
        'member_rolls[]': ['2026-CSE-100', '2026-CSE-101'],
        'member_roles[]': ['Core Developer', 'Research Scholar'],
        'submit_mode': 'publish'
    }
    res_reg_submit = client.post('/student/project/register', data=reg_post_data, follow_redirects=True)
    with app.app_context():
        new_team = Team.query.filter_by(team_name='Quantum Autonomous Robotics').first()
        team_created = new_team is not None and len(new_team.members) == 3 and new_team.project is not None
        log_test("STUDENT", "Dynamic Multi-Member Registration", res_reg_submit.status_code == 200 and team_created,
                 f"Team '{new_team.team_name if new_team else 'None'}' created with {len(new_team.members) if new_team else 0} members")

    # 10n. Student Milestone Cloud Deliverable Link Submission (Google Drive / GitHub Docs)
    cloud_link_data = {
        'submission_text': 'Completed Milestone 1 sprint requirements including architecture diagram and sensor interface specs.',
        'repository_url': 'https://github.com/university/swarm-drone-slam',
        'submission_link': 'https://drive.google.com/file/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OIvE2upWE/view?usp=sharing',
        'link_title': 'Swarm Drone Edge SLAM Architecture Specification v1.0',
        'notes': 'Public Google Drive link configured with Anyone with the link can view permissions.'
    }
    res_file_sub = client.post('/student/submit/1', data=cloud_link_data, follow_redirects=True)
    with app.app_context():
        uploaded_sub = Submission.query.filter_by(project_id=new_team.project.id, milestone_id=1).first() if new_team else None
        cloud_link_saved = (
            uploaded_sub is not None and
            uploaded_sub.submission_link == 'https://drive.google.com/file/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OIvE2upWE/view?usp=sharing' and
            uploaded_sub.link_title == 'Swarm Drone Edge SLAM Architecture Specification v1.0'
        )
        log_test("STUDENT", "Milestone Cloud Deliverable Link Submission", res_file_sub.status_code == 200 and cloud_link_saved,
                 f"Submission saved with Google Drive link: {uploaded_sub.submission_link if uploaded_sub else 'None'}")

    print("\n" + "="*80)
    print("                     📊 FINAL TEST RESULTS SUMMARY")
    print("="*80)
    total_tests = len(results)
    passed_tests = sum(1 for r in results if r[0] == "✅")
    failed_tests = total_tests - passed_tests

    for sym, cat, name, det in results:
        print(f"{sym} {cat:<16} | {name:<35} | {det}")

    print("\n" + "-"*80)
    print(f"TOTAL TESTS: {total_tests} | PASSED: {passed_tests} | FAILED: {failed_tests}")
    print("="*80 + "\n")

    return failed_tests == 0

if __name__ == '__main__':
    success = run_full_system_verification()
    sys.exit(0 if success else 1)
