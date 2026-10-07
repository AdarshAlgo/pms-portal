"""
Seed script to initialize and populate the Project Progress Monitoring & Evaluation System.
Populates:
- 3 Dedicated Users (Admin, Faculty: Dr. Ankit Verma, Student: Adarsh Katiyar)
- 5 Realistic Capstone Projects guided by Dr. Ankit Verma with Lead Adarsh Katiyar
- 4 Standard Academic Milestones
- Rich Rubrics, Submissions, Evaluation Scores, Meeting Logs, and Feedback
"""

from datetime import datetime, date, timedelta
from app import create_app
from app.extensions import db, bcrypt
from app.models.user import Role, User
from app.models.project import Department, AcademicTerm, Team, TeamMember, Project
from app.models.milestone import Milestone, Submission, MilestoneDeadlineOverride
from app.models.evaluation import RubricTemplate, RubricCriteria, EvaluationScore, GradeBoundary
from app.models.feedback import FeedbackLog, MeetingLog, Notification, ActivityLog, AuditLog, SystemSetting

def create_default_users(roles=None, depts=None):
    """
    Creates or updates the default initial production-grade accounts:
    1. Admin Account:
       - Name: System Administrator
       - Username: admin_pms
       - Email: admin@university.edu
       - Password: Admin@PMS2026#Secure
       - Role: admin
    2. Faculty Guide Account:
       - Name: Dr. Ankit Verma
       - Username: dr_ankit_verma
       - Email: dr.verma@university.edu
       - Password: Faculty@Verma2026!
       - Role: faculty
    3. Lead Student Account:
       - Name: Adarsh Katiyar
       - Username: adarsh_lead
       - Email: student1@university.edu
       - Password: Student@Katiyar2026!
       - Role: student
    """
    if roles is None:
        roles = {r.role_name: r for r in Role.query.all()}
    if depts is None:
        depts = {d.code: d for d in Department.query.all()}

    default_users_data = [
        # (email, username, first_name, last_name, role_name, dept_code, enroll, perm_level, can_eval, can_sub, password)
        (
            'admin@university.edu',
            'admin_pms',
            'System',
            'Administrator',
            'admin',
            'ADM',
            None,
            'full',
            True,
            True,
            'Admin@PMS2026#Secure'
        ),
        (
            'dr.verma@university.edu',
            'dr_ankit_verma',
            'Dr. Ankit',
            'Verma',
            'faculty',
            'CSE',
            None,
            'full',
            True,
            False,
            'Faculty@Verma2026!'
        ),
        (
            'student1@university.edu',
            'adarsh_lead',
            'Adarsh',
            'Katiyar',
            'student',
            'CSE',
            'CSE2026001',
            'standard',
            False,
            True,
            'Student@Katiyar2026!'
        ),
    ]

    users = {}
    now = datetime.utcnow()
    for email, username, fn, ln, rname, dept_code, enroll, perm_level, can_eval, can_sub, raw_pwd in default_users_data:
        dept_obj = depts.get(dept_code)
        dept_name = dept_obj.name if dept_obj else None
        dept_id = dept_obj.id if dept_obj else None
        role_obj = roles.get(rname)
        role_id = role_obj.id if role_obj else 1

        # Check existing user by email OR username to safely update in place
        user = User.query.filter(
            db.or_(User.email == email, User.username == username)
        ).first()

        if not user:
            user = User(
                username=username,
                email=email,
                first_name=fn,
                last_name=ln,
                role_id=role_id,
                department=dept_name,
                department_id=dept_id,
                enrollment_number=enroll,
                is_active=True,
                is_verified=True,
                status='active',
                permission_level=perm_level,
                can_evaluate=can_eval,
                can_submit=can_sub,
                last_seen_at=now - timedelta(minutes=5)
            )
            user.set_password(raw_pwd)
            db.session.add(user)
            db.session.flush()
        else:
            user.username = username
            user.email = email
            user.first_name = fn
            user.last_name = ln
            user.role_id = role_id
            user.department = dept_name
            user.department_id = dept_id
            user.enrollment_number = enroll
            user.is_active = True
            user.is_verified = True
            user.status = 'active'
            user.permission_level = perm_level
            user.can_evaluate = can_eval
            user.can_submit = can_sub
            user.set_password(raw_pwd)
            db.session.flush()

        users[email] = user

    return users

def seed_database(reset=True):
    app = create_app('development')
    with app.app_context():
        if reset:
            print("Resetting database schema...")
            db.drop_all()
        print("Creating all database tables...")
        db.create_all()
        now = datetime.utcnow()

        # ---------------------------------------------------------
        # 1. ROLES
        # ---------------------------------------------------------
        roles_data = [
            ('admin', 'System Administrator with full institutional governance'),
            ('faculty', 'Faculty member who guides and evaluates capstone projects'),
            ('student', 'Student enrolled in capstone project groups')
        ]
        roles = {}
        for name, desc in roles_data:
            role = Role.query.filter_by(role_name=name).first()
            if not role:
                role = Role(role_name=name, description=desc)
                db.session.add(role)
                db.session.flush()
            roles[name] = role

        # ---------------------------------------------------------
        # 2. DEPARTMENTS
        # ---------------------------------------------------------
        depts_data = [
            ('Master of Computer Applications (MCA)', 'MCA'),
            ('Computer Science & Engineering', 'CSE'),
            ('Information Technology', 'IT'),
            ('Electronics & Robotics', 'ECE'),
            ('Academic Administration', 'ADM')
        ]
        depts = {}
        for name, code in depts_data:
            dept = Department.query.filter_by(code=code).first()
            if not dept:
                dept = Department(name=name, code=code)
                db.session.add(dept)
                db.session.flush()
            else:
                dept.name = name
                db.session.flush()
            depts[code] = dept

        # ---------------------------------------------------------
        # 3. USERS (ADMIN, FACULTY, STUDENT) WITH SECURE PRODUCTION PASSWORDS
        # ---------------------------------------------------------
        users = create_default_users(roles, depts)

        # Assign Department Heads (All departments mentored under Dr. Ankit Verma)
        if 'MCA' in depts:
            depts['MCA'].head_of_department_id = users['dr.verma@university.edu'].id
        depts['CSE'].head_of_department_id = users['dr.verma@university.edu'].id
        depts['IT'].head_of_department_id = users['dr.verma@university.edu'].id
        depts['ECE'].head_of_department_id = users['dr.verma@university.edu'].id

        # ---------------------------------------------------------
        # 4. ACADEMIC TERM
        # ---------------------------------------------------------
        term = AcademicTerm.query.filter_by(term_name='Academic Year 2025-2026').first()
        if not term:
            term = AcademicTerm(
                term_name='Academic Year 2025-2026',
                start_date=date(2025, 8, 1),
                end_date=date(2026, 5, 30),
                is_current=True,
                created_by=users['admin@university.edu'].id
            )
            db.session.add(term)
            db.session.flush()

        # ---------------------------------------------------------
        # 5. GLOBAL MILESTONES (4 PHASES)
        # ---------------------------------------------------------
        milestones_data = [
            (1, 'Milestone 1: Project Synopsis & Architecture',
             'System architecture diagram, SRS specification, feasibility study, and literature survey.',
             date(2025, 9, 20), 10.0),
            (2, 'Milestone 2: Database Schema & Low-Level Design',
             '3NF Normalized MySQL DDL schema, ER diagram, module interaction flow, and API contracts.',
             date(2025, 11, 15), 15.0),
            (3, 'Milestone 3: Implementation & Prototype Core',
             'Functional core backend services, machine learning model weights, REST endpoints, and prototype UI.',
             date(2026, 1, 25), 20.0),
            (4, 'Milestone 4: Final Verification, Testing & Defense',
             'End-to-end integration testing, performance benchmarks, final defense presentation, and thesis report.',
             date(2026, 4, 15), 25.0)
        ]
        milestones = []
        for order, title, desc, ddate, weight in milestones_data:
            ms = Milestone.query.filter_by(milestone_order=order, academic_term_id=term.id).first()
            if not ms:
                ms = Milestone(
                    academic_term_id=term.id,
                    title=title,
                    description=desc,
                    deadline=datetime.combine(ddate, datetime.min.time()),
                    milestone_order=order,
                    weightage_percent=weight,
                    is_mandatory=True,
                    is_custom=False,
                    approval_status='approved',
                    deliverable_type='Report',
                    created_by=users['admin@university.edu'].id
                )
                db.session.add(ms)
                db.session.flush()
            else:
                ms.is_custom = False
                ms.approval_status = ms.approval_status or 'approved'
            milestones.append(ms)

        # ---------------------------------------------------------
        # 6. RUBRIC TEMPLATE & CRITERIA
        # ---------------------------------------------------------
        rubric = RubricTemplate.query.filter_by(academic_term_id=term.id).first()
        if not rubric:
            rubric = RubricTemplate(
                name='National Institutional Evaluation Rubric (NIRF/NBA)',
                description='Comprehensive criterion-based institutional grading rubric.',
                academic_term_id=term.id,
                created_by=users['admin@university.edu'].id,
                is_active=True
            )
            db.session.add(rubric)
            db.session.flush()

            criteria_data = [
                ('Technical Depth & Innovation', 'Originality of solution, technological complexity, and modern methodology.', 10.0, 25.0, 1),
                ('Implementation & Code Quality', 'System architecture, clean modular code, API correctness, and test coverage.', 10.0, 40.0, 2),
                ('Documentation & SRS Standards', 'Completeness of diagrams, technical documentation, and IEEE reporting standards.', 10.0, 20.0, 3),
                ('Presentation & Viva Defense', 'Clarity of live demonstration, answers to technical cross-questions, and team coordination.', 10.0, 15.0, 4)
            ]
            for cname, cdesc, max_m, weight, dorder in criteria_data:
                crit = RubricCriteria(
                    rubric_template_id=rubric.id,
                    criterion_name=cname,
                    description=cdesc,
                    max_marks=max_m,
                    weightage=weight,
                    display_order=dorder
                )
                db.session.add(crit)
            db.session.flush()

        criteria = RubricCriteria.query.filter_by(rubric_template_id=rubric.id).order_by(RubricCriteria.display_order).all()

        # ---------------------------------------------------------
        # 7. 5 REALISTIC CAPSTONE PROJECTS & TEAMS
        # ---------------------------------------------------------
        projects_seed = [
            {
                'team_name': 'Team Agrotech Innovators',
                'lead': users['student1@university.edu'],
                'guide': users['dr.verma@university.edu'],
                'dept': 'Computer Science & Engineering',
                'title': 'AI-Driven Crop Disease Detection & Advisory System (Krishi-Drishti)',
                'abstract': 'Deep learning edge-computing system utilizing lightweight CNN architectures (MobileNetV3) deployed on low-power devices for real-time foliar pathology identification in rural Indian farms.',
                'objectives': '1. Train CNN on 54,000 foliar pathology images.\n2. Achieve >94% validation accuracy.\n3. Build low-latency Flask REST API for edge inference.',
                'progress_milestones': 2, # 2/4 completed (M1 & M2 approved, M3 open for submission)
                'scores': [
                    [9.5, 9.0, 9.5, 9.0], # M1
                    [9.0, 9.5, 9.0, 9.5], # M2
                ]
            },
            {
                'team_name': 'Team Kavach Mobility',
                'lead': users['student1@university.edu'],
                'guide': users['dr.verma@university.edu'],
                'dept': 'Information Technology',
                'title': 'Kavach: Smart Highway Telemetry & Collision Prevention System',
                'abstract': 'V2X cellular telemetry and ultrasonic radar sensor array integrating Kalman filters to prevent multi-vehicle highway pile-ups and automate SOS geolocation alerts.',
                'objectives': '1. Design low-latency V2X telemetry transceiver.\n2. Implement predictive collision trajectory algorithm.\n3. Integrate automated emergency response dispatch API.',
                'progress_milestones': 4, # 4/4 completed (100%)
                'scores': [
                    [9.0, 8.5, 9.0, 8.5], # M1
                    [8.5, 9.0, 8.5, 9.0], # M2
                    [9.0, 8.5, 9.0, 8.5], # M3
                    [9.5, 9.0, 9.0, 9.5], # M4
                ]
            },
            {
                'team_name': 'Team AquaRobotics',
                'lead': users['student1@university.edu'],
                'guide': users['dr.verma@university.edu'],
                'dept': 'Electronics & Robotics',
                'title': 'Jal-Drishti: Autonomous River Water Quality Monitoring Drone',
                'abstract': 'Autonomous aquatic drone catamaran equipped with multi-parameter sensor arrays (pH, Turbidity, Dissolved Oxygen) and LoRaWAN long-range telemetry for continuous Ganga basin pollution mapping.',
                'objectives': '1. Construct solar-powered autonomous catamaran hull.\n2. Calibrate sensor telemetry pipeline over 15km LoRaWAN link.\n3. Create real-time GIS river pollution heat-map dashboard.',
                'progress_milestones': 2, # 2/4 completed (50%), M3 submitted
                'scores': [
                    [8.5, 8.5, 8.0, 8.5], # M1
                    [8.0, 8.5, 8.5, 8.0], # M2
                ]
            },
            {
                'team_name': 'Team UrjaGrid',
                'lead': users['student1@university.edu'],
                'guide': users['dr.verma@university.edu'],
                'dept': 'Computer Science & Engineering',
                'title': 'Urja-Net: Decentralized Peer-to-Peer Solar Microgrid Trading',
                'abstract': 'Smart-contract enabled microgrid market platform enabling rooftop solar prosumers to trade surplus kilowatt-hours securely with dynamic local algorithmic load balancing.',
                'objectives': '1. Formulate dynamic pricing smart contract.\n2. Build IoT bidirectional smart meter telemetry bridge.\n3. Simulate grid stability under volatile peak demand.',
                'progress_milestones': 1, # 1/4 completed (25%), M2 under review
                'scores': [
                    [8.5, 8.0, 8.0, 8.5], # M1
                ]
            },
            {
                'team_name': 'Team Swasthya Tech',
                'lead': users['student1@university.edu'],
                'guide': users['dr.verma@university.edu'],
                'dept': 'Information Technology',
                'title': 'Swasthya-AI: Deep Learning Diagnostic Scanner for Rural Health Kiosks',
                'abstract': 'Affordable computer-vision medical kiosk for rapid screening of diabetic retinopathy and pulmonary radiography abnormalities in underserved rural clinics.',
                'objectives': '1. Train multi-modal CNN for retinal fundus and chest X-ray screening.\n2. Package into offline touchscreen kiosk system.\n3. Validate diagnostic sensitivity with clinical gold standards.',
                'progress_milestones': 2, # 2/4 completed (50%), M3 in progress
                'scores': [
                    [9.0, 8.5, 9.0, 9.0], # M1
                    [8.5, 9.0, 8.5, 8.5], # M2
                ]
            }
        ]

        dept_map = {
            'Computer Science & Engineering': 'CSE',
            'Information Technology': 'IT',
            'Electronics & Robotics': 'ECE'
        }

        for pdata in projects_seed:
            team = Team.query.filter_by(team_name=pdata['team_name']).first()
            if not team:
                dcode = dept_map.get(pdata['dept'], 'CSE')
                team = Team(
                    team_name=pdata['team_name'],
                    academic_term_id=term.id,
                    department_id=depts[dcode].id,
                    guide_id=pdata['guide'].id
                )
                db.session.add(team)
                db.session.flush()

                # Add Lead Member
                tm = TeamMember(team_id=team.id, user_id=pdata['lead'].id, role_in_team='Leader')
                db.session.add(tm)

            project = Project.query.filter_by(team_id=team.id).first()
            if not project:
                project = Project(
                    team_id=team.id,
                    title=pdata['title'],
                    abstract=pdata['abstract'],
                    objectives=pdata['objectives'],
                    domain=pdata['dept'],
                    technology_stack='Python, Flask, PyTorch, MySQL, Tailwind CSS',
                    sdg_alignment='UN SDG 9: Industry, Innovation & Infrastructure',
                    status='approved',
                    approved_by=pdata['guide'].id,
                    approved_at=now - timedelta(days=90)
                )
                db.session.add(project)
                db.session.flush()

            # Create Submissions and Evaluated Scores
            for m_idx in range(pdata['progress_milestones']):
                ms = milestones[m_idx]
                sub = Submission.query.filter_by(project_id=project.id, milestone_id=ms.id).first()
                if not sub:
                    sub = Submission(
                        project_id=project.id,
                        milestone_id=ms.id,
                        submitted_by=pdata['lead'].id,
                        submission_text=f"Formal deliverable submission for {ms.title}. Comprehensive engineering documentation, architecture diagrams, and repository code links attached.",
                        submission_link=f"https://drive.google.com/institutional-repo/{pdata['team_name'].lower().replace(' ', '-')}/m{ms.milestone_order}-report.pdf",
                        document_url=f"https://drive.google.com/institutional-repo/{pdata['team_name'].lower().replace(' ', '-')}/m{ms.milestone_order}-report.pdf",
                        repository_url=f"https://github.com/academic-projects-2026/{pdata['team_name'].lower().replace(' ', '-')}",
                        status='approved',
                        submitted_at=now - timedelta(days=(4 - m_idx) * 20),
                        reviewed_by=pdata['guide'].id,
                        reviewed_at=now - timedelta(days=(4 - m_idx) * 20 - 2)
                    )
                    db.session.add(sub)
                    db.session.flush()

                    # Add Rubric Scores
                    m_scores = pdata['scores'][m_idx]
                    for c_idx, crit in enumerate(criteria):
                        mark = m_scores[c_idx]
                        es = EvaluationScore(
                            submission_id=sub.id,
                            rubric_criteria_id=crit.id,
                            evaluator_id=pdata['guide'].id,
                            marks_obtained=mark,
                            remarks=f"Demonstrated high engineering fidelity in {crit.criterion_name.lower()}."
                        )
                        db.session.add(es)

                    # Add Feedback Log
                    flog = FeedbackLog(
                        submission_id=sub.id,
                        author_id=pdata['guide'].id,
                        feedback_type='approval',
                        content=f"Approved with commendation. Excellent progress on {ms.title}."
                    )
                    db.session.add(flog)

            # If project has a pending submission for the next milestone (skip Project 1 to test live submission)
            if pdata['progress_milestones'] < 4 and pdata != projects_seed[0]:
                next_ms = milestones[pdata['progress_milestones']]
                sub_next = Submission.query.filter_by(project_id=project.id, milestone_id=next_ms.id).first()
                if not sub_next:
                    sub_status = 'submitted' if pdata['progress_milestones'] % 2 == 1 else 'under_review'
                    sub_next = Submission(
                        project_id=project.id,
                        milestone_id=next_ms.id,
                        submitted_by=pdata['lead'].id,
                        submission_text=f"Draft deliverables for {next_ms.title} uploaded for faculty review and evaluation.",
                        submission_link=f"https://drive.google.com/institutional-repo/{pdata['team_name'].lower().replace(' ', '-')}/draft-report.pdf",
                        document_url=f"https://drive.google.com/institutional-repo/{pdata['team_name'].lower().replace(' ', '-')}/draft-report.pdf",
                        repository_url=f"https://github.com/academic-projects-2026/{pdata['team_name'].lower().replace(' ', '-')}/tree/dev",
                        status=sub_status,
                        submitted_at=now - timedelta(days=2)
                    )
                    db.session.add(sub_next)

            # Meeting Logs
            mlog = MeetingLog(
                team_id=team.id,
                scheduled_by=pdata['guide'].id,
                meeting_date=date.today() - timedelta(days=7),
                duration_minutes=45,
                agenda=f"Sprint review and architectural audit for {pdata['team_name']}.",
                minutes="Reviewed sprint velocity, verified experimental benchmarks, and resolved API integration blockers.",
                status='completed'
            )
            db.session.add(mlog)

        # ---------------------------------------------------------
        # 8. ACTIVITY & AUDIT LOGS
        # ---------------------------------------------------------
        activities = [
            (users['dr.verma@university.edu'].id, 'evaluate_submission', 'Evaluated Milestone 3 for Team Agrotech Innovators with 94%'),
            (users['dr.verma@university.edu'].id, 'review_submission', 'Approved Milestone 3 deliverable for Team Kavach Mobility'),
            (users['admin@university.edu'].id, 'system_config', 'Updated National Institutional Evaluation Rubric weightages'),
            (users['student1@university.edu'].id, 'submit_milestone', 'Submitted Milestone 4 Final Defense documentation'),
            (users['dr.verma@university.edu'].id, 'meeting_logged', 'Completed bi-weekly review meeting with Team AquaRobotics')
        ]
        for uid, action, details in activities:
            act = ActivityLog(user_id=uid, action=action, details=details, ip_address='127.0.0.1')
            db.session.add(act)
            audit = AuditLog(user_id=uid, action=action, details=details, ip_address='127.0.0.1')
            db.session.add(audit)

        # ---------------------------------------------------------
        # 9. GRADE BOUNDARIES & SYSTEM SETTINGS
        # ---------------------------------------------------------
        boundaries_data = [
            ('A+', 90.0, 'Exemplary Mastery', 1),
            ('A', 80.0, 'Proficient / Commendable', 2),
            ('B+', 70.0, 'Good / Meritorious', 3),
            ('B', 60.0, 'Satisfactory', 4),
            ('C', 50.0, 'Developing / Minimum Pass', 5),
            ('F', 0.0, 'Unsatisfactory / Fail', 6)
        ]
        for letter, min_pct, desc, order in boundaries_data:
            gb = GradeBoundary.query.filter_by(grade_letter=letter).first()
            if not gb:
                gb = GradeBoundary(grade_letter=letter, min_percentage=min_pct, description=desc, display_order=order)
                db.session.add(gb)

        SystemSetting.set('MAX_FILE_SIZE_MB', '32', 'Maximum upload file size in megabytes')
        SystemSetting.set('ALLOWED_EXTENSIONS', 'pdf,zip,docx,pptx', 'Allowed file upload extensions')
        SystemSetting.set('SUBMISSIONS_LOCKED', 'false', 'Master lock for student milestone submissions')
        SystemSetting.set('FACULTY_MAX_COHORTS', '5', 'Max quota of cohorts per faculty guide')

        db.session.commit()
        print("✅ Database successfully populated with Admin, Dr. Ankit Verma, Adarsh Katiyar, 5 projects, and full evaluation analytics!")

if __name__ == '__main__':
    seed_database(reset=True)
