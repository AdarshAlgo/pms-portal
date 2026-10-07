"""
Database Inspector Script.
Run this script anytime to see tables, counts, and contents of the database:
    python view_db.py
"""

from app import create_app
from app.extensions import db
from app.models.user import Role, User
from app.models.project import Department, AcademicTerm, Team, TeamMember, Project
from app.models.milestone import Milestone, Submission
from app.models.evaluation import RubricTemplate, RubricCriteria, EvaluationScore
from app.models.feedback import FeedbackLog, MeetingLog

def inspect_database():
    app = create_app()
    with app.app_context():
        print("=" * 70)
        print("         PROJECT PROGRESS MONITORING SYSTEM - DATABASE VIEWER")
        print("=" * 70)

        # 1. Users
        print("\n👥 [1. USERS & ROLES]")
        print("-" * 70)
        users = User.query.all()
        for u in users:
            role_name = u.role.role_name.upper() if u.role else 'NO ROLE'
            print(f"ID: {u.id:<2} | {u.full_name:<18} | {u.email:<26} | Role: {role_name:<7} | Dept: {u.department or 'N/A'}")

        # 2. Projects & Teams
        print("\n🚀 [2. TEAMS & CAPSTONE PROJECTS]")
        print("-" * 70)
        projects = Project.query.all()
        for p in projects:
            guide = User.query.get(p.team.guide_id) if p.team and p.team.guide_id else None
            guide_name = guide.full_name if guide else "Unassigned"
            print(f"Project #{p.id}: {p.title}")
            print(f"  Team: {p.team.team_name} | Guide: {guide_name} | Status: {p.status.upper()} | SDG: {p.sdg_alignment}")
            print(f"  Domain: {p.domain} | Tech Stack: {p.technology_stack}")

        # 3. Milestones
        print("\n🎯 [3. ACADEMIC MILESTONES]")
        print("-" * 70)
        milestones = Milestone.query.order_by(Milestone.milestone_order).all()
        for m in milestones:
            d_str = m.deadline.strftime('%Y-%m-%d') if m.deadline else 'No deadline'
            print(f"Milestone {m.milestone_order}: {m.title:<30} | Weight: {m.weightage_percent}% | Deadline: {d_str}")

        # 4. Submissions & Evaluations
        print("\n📝 [4. STUDENT SUBMISSIONS & EVALUATION SCORES]")
        print("-" * 70)
        submissions = Submission.query.all()
        for s in submissions:
            m_title = s.milestone.title if s.milestone else f"M#{s.milestone_id}"
            submitter = s.submitter.full_name if s.submitter else f"User#{s.submitted_by}"
            print(f"Submission #{s.id} for [{m_title}] by {submitter}:")
            print(f"  Status: {s.status.upper()} | Revisions: {s.revision_count}")
            print(f"  Text: {s.submission_text[:80]}...")
            
            # Scores
            scores = EvaluationScore.query.filter_by(submission_id=s.id).all()
            if scores:
                print("  Rubric Criteria Scores:")
                total_m = 0
                max_m = 0
                for sc in scores:
                    crit = RubricCriteria.query.get(sc.rubric_criteria_id)
                    c_name = crit.criterion_name if crit else f"Crit#{sc.rubric_criteria_id}"
                    c_max = crit.max_marks if crit else 10.0
                    total_m += sc.marks_obtained
                    max_m += c_max
                    print(f"    • {c_name:<32}: {sc.marks_obtained:>4.1f} / {c_max:<4.1f} marks (Remarks: {sc.remarks})")
                pct = (total_m / max_m * 100) if max_m > 0 else 0
                print(f"  Total Score: {total_m:.1f}/{max_m:.1f} ({pct:.1f}%)")
            else:
                print("  No rubric scores assigned yet.")

        # 5. Feedback & Meetings
        print("\n💬 [5. FEEDBACK LOGS & AUDIT TRAIL]")
        print("-" * 70)
        feedbacks = FeedbackLog.query.all()
        for f in feedbacks:
            author = User.query.get(f.author_id)
            aname = author.full_name if author else f"User#{f.author_id}"
            print(f"[{f.feedback_type.upper()}] from {aname}: \"{f.content}\"")

        print("=" * 70)

if __name__ == '__main__':
    inspect_database()
