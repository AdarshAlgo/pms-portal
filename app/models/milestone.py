from datetime import datetime
from app.extensions import db

class Milestone(db.Model):
    __tablename__ = 'milestones'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text)
    milestone_order = db.Column(db.Integer, nullable=False)
    academic_term_id = db.Column(db.Integer, db.ForeignKey('academic_terms.id'), nullable=False)
    deadline = db.Column(db.DateTime, nullable=False)
    grace_period_deadline = db.Column(db.DateTime)
    weightage_percent = db.Column(db.Float, default=0.0)
    is_mandatory = db.Column(db.Boolean, default=True)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Dynamic Custom Milestones Engine Fields
    is_custom = db.Column(db.Boolean, default=False)
    created_by_student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=True)
    approval_status = db.Column(db.String(50), default='approved')  # 'pending_review', 'approved', 'rejected'
    deliverable_type = db.Column(db.String(50), default='Report')  # 'Report', 'Prototype', 'Code', 'API'
    faculty_feedback = db.Column(db.Text, nullable=True)

    overrides = db.relationship('MilestoneDeadlineOverride', backref='milestone', lazy=True, cascade='all, delete-orphan')
    created_by_student = db.relationship('User', foreign_keys=[created_by_student_id], backref='custom_milestones_created')
    project = db.relationship('Project', foreign_keys=[project_id], backref=db.backref('custom_milestones', lazy=True, cascade='all, delete-orphan'))

    def get_effective_deadline(self, team_id=None):
        """Returns team-specific extended deadline if granted, otherwise global deadline."""
        if team_id:
            override = MilestoneDeadlineOverride.query.filter_by(milestone_id=self.id, team_id=team_id).first()
            if override and override.extended_deadline:
                return override.extended_deadline
        return self.grace_period_deadline or self.deadline

class MilestoneDeadlineOverride(db.Model):
    __tablename__ = 'milestone_deadline_overrides'
    id = db.Column(db.Integer, primary_key=True)
    milestone_id = db.Column(db.Integer, db.ForeignKey('milestones.id'), nullable=False)
    team_id = db.Column(db.Integer, db.ForeignKey('teams.id'), nullable=False)
    extended_deadline = db.Column(db.DateTime, nullable=False)
    reason = db.Column(db.String(255))
    granted_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    team = db.relationship('Team', backref=db.backref('deadline_overrides', lazy=True))
    granter = db.relationship('User', foreign_keys=[granted_by], backref='granted_deadline_overrides')

    __table_args__ = (
        db.UniqueConstraint('milestone_id', 'team_id', name='uq_milestone_team_override'),
    )

class Submission(db.Model):
    __tablename__ = 'submissions'
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    milestone_id = db.Column(db.Integer, db.ForeignKey('milestones.id'), nullable=False)
    submitted_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    submission_text = db.Column(db.Text)
    submission_link = db.Column(db.String(500), nullable=True)  # Cloud link (Google Drive / GitHub Docs)
    link_title = db.Column(db.String(255), nullable=True)       # Optional link title
    notes = db.Column(db.Text, nullable=True)                   # Optional notes
    document_url = db.Column(db.String(500), nullable=True)     # Retained for backwards compatibility
    repository_url = db.Column(db.String(255))
    status = db.Column(db.String(50), default='pending')  # 'pending', 'submitted', 'under_review', 'revision_required', 'approved', 'rejected'
    version = db.Column(db.Integer, default=1)
    is_late = db.Column(db.Boolean, default=False)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    reviewed_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    reviewed_at = db.Column(db.DateTime)
    revision_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    project = db.relationship('Project', backref=db.backref('submissions', lazy=True, cascade='all, delete-orphan'))
    milestone = db.relationship('Milestone', backref=db.backref('submissions', lazy=True))
    submitter = db.relationship('User', foreign_keys=[submitted_by], backref='submissions')
    reviewer = db.relationship('User', foreign_keys=[reviewed_by], backref='reviewed_submissions')

    __table_args__ = (
        db.UniqueConstraint('project_id', 'milestone_id', name='uq_project_milestone_submission'),
    )

    @property
    def deliverable_url(self):
        return self.submission_link or self.document_url or self.repository_url

    @property
    def file_attachment_url(self):
        return self.submission_link or self.document_url

    @file_attachment_url.setter
    def file_attachment_url(self, val):
        self.submission_link = val
        self.document_url = val

    @property
    def file_url(self):
        return self.submission_link or self.document_url or self.repository_url

    @property
    def github_url(self):
        return self.repository_url

    @github_url.setter
    def github_url(self, val):
        self.repository_url = val
