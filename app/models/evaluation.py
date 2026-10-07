from datetime import datetime
from app.extensions import db

class RubricTemplate(db.Model):
    __tablename__ = 'rubric_templates'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text)
    academic_term_id = db.Column(db.Integer, db.ForeignKey('academic_terms.id'))
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    criteria = db.relationship('RubricCriteria', backref='template', lazy=True, cascade='all, delete-orphan')

class RubricCriteria(db.Model):
    __tablename__ = 'rubric_criteria'
    id = db.Column(db.Integer, primary_key=True)
    rubric_template_id = db.Column(db.Integer, db.ForeignKey('rubric_templates.id'), nullable=False)
    criterion_name = db.Column(db.String(150), nullable=False)
    max_marks = db.Column(db.Float, nullable=False)
    weightage = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text)
    display_order = db.Column(db.Integer, default=0)
    # Performance descriptors (JSON or structured text)
    exemplary_desc = db.Column(db.Text, default='Demonstrates complete mastery, zero architectural defects, exemplary technical rigor.')
    proficient_desc = db.Column(db.Text, default='Clear and complete implementation meeting all stated technical requirements.')
    developing_desc = db.Column(db.Text, default='Partial implementation with minor gaps in documentation or test execution.')
    unsatisfactory_desc = db.Column(db.Text, default='Significant architectural deficiencies or non-functional deliverables.')

class EvaluationScore(db.Model):
    __tablename__ = 'evaluation_scores'
    id = db.Column(db.Integer, primary_key=True)
    submission_id = db.Column(db.Integer, db.ForeignKey('submissions.id'), nullable=False)
    rubric_criteria_id = db.Column(db.Integer, db.ForeignKey('rubric_criteria.id'), nullable=True)
    evaluator_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    marks_obtained = db.Column(db.Float, default=0.0)
    remarks = db.Column(db.Text)
    # Master Override / Evaluation Summary attributes
    total_percentage = db.Column(db.Float)
    grade = db.Column(db.String(10))
    feedback_summary = db.Column(db.Text)
    is_overridden_by_admin = db.Column(db.Boolean, default=False)
    override_reason = db.Column(db.String(255))
    evaluated_at = db.Column(db.DateTime, default=datetime.utcnow)

    submission = db.relationship('Submission', backref=db.backref('evaluation_scores', lazy=True, cascade='all, delete-orphan'))
    criterion = db.relationship('RubricCriteria', backref=db.backref('evaluation_scores', lazy=True))
    evaluator = db.relationship('User', foreign_keys=[evaluator_id], backref='evaluations_performed')

    __table_args__ = (
        db.UniqueConstraint('submission_id', 'rubric_criteria_id', 'evaluator_id', name='uq_evaluation_score'),
    )

class GradeBoundary(db.Model):
    __tablename__ = 'grade_boundaries'
    id = db.Column(db.Integer, primary_key=True)
    grade_letter = db.Column(db.String(10), unique=True, nullable=False)  # 'A+', 'A', 'B+', 'B', 'C', 'F'
    min_percentage = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(150))
    display_order = db.Column(db.Integer, default=0)

class ExternalJuryAssignment(db.Model):
    __tablename__ = 'external_jury_assignments'
    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey('teams.id'), nullable=False)
    milestone_id = db.Column(db.Integer, db.ForeignKey('milestones.id'), nullable=True)
    jury_name = db.Column(db.String(120), nullable=False)
    jury_email = db.Column(db.String(120), nullable=False)
    organization = db.Column(db.String(150))
    specialization = db.Column(db.String(150))
    assigned_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    assigned_at = db.Column(db.DateTime, default=datetime.utcnow)

    team = db.relationship('Team', backref='jury_assignments')
    granter = db.relationship('User', foreign_keys=[assigned_by])
