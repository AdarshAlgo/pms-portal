from datetime import datetime
from app.extensions import db

class Department(db.Model):
    __tablename__ = 'departments'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(20), unique=True, nullable=False)
    head_of_department_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    @classmethod
    def get_ordered(cls):
        """Returns departments with MCA prioritized at the top, followed by alphabetical order."""
        return cls.query.order_by(
            db.case((cls.code == 'MCA', 1), else_=2),
            cls.name.asc()
        ).all()

class AcademicTerm(db.Model):
    __tablename__ = 'academic_terms'
    id = db.Column(db.Integer, primary_key=True)
    term_name = db.Column(db.String(100), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    is_current = db.Column(db.Boolean, default=False)
    is_locked = db.Column(db.Boolean, default=False)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Team(db.Model):
    __tablename__ = 'teams'
    id = db.Column(db.Integer, primary_key=True)
    team_name = db.Column(db.String(100), nullable=False)
    academic_term_id = db.Column(db.Integer, db.ForeignKey('academic_terms.id'))
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'))
    guide_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    status = db.Column(db.String(50), default='active')  # 'draft', 'approved', 'active', 'archived'
    max_members = db.Column(db.Integer, default=4)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    members = db.relationship('TeamMember', backref='team', lazy=True, cascade='all, delete-orphan')
    project = db.relationship('Project', backref='team', uselist=False, lazy=True, cascade='all, delete-orphan')
    guide = db.relationship('User', foreign_keys=[guide_id], backref='guided_teams')
    department = db.relationship('Department', backref='teams')
    academic_term = db.relationship('AcademicTerm', backref='teams')

    @property
    def leader(self):
        for m in self.members:
            if m.role_in_team and m.role_in_team.lower() in ('leader', 'team leader'):
                return m
        return self.members[0] if self.members else None

class TeamMember(db.Model):
    __tablename__ = 'team_members'
    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey('teams.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # nullable for prospective/invited members
    student_name = db.Column(db.String(100))
    student_email = db.Column(db.String(120))
    roll_number = db.Column(db.String(50))
    role_in_team = db.Column(db.String(50), default='Core Developer')  # 'Leader', 'Core Developer', 'Research Scholar'
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='team_memberships')

    @property
    def display_name(self):
        if self.user:
            return self.user.full_name
        return self.student_name or 'Unregistered Scholar'

    @property
    def display_email(self):
        if self.user:
            return self.user.email
        return self.student_email or 'N/A'

class Project(db.Model):
    __tablename__ = 'projects'
    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey('teams.id'), nullable=False, unique=True)
    title = db.Column(db.String(255), nullable=False)
    abstract = db.Column(db.Text)
    objectives = db.Column(db.Text)
    domain = db.Column(db.String(100))
    technology_stack = db.Column(db.String(255))
    sdg_alignment = db.Column(db.String(255), default='SDG 9')
    repo_url = db.Column(db.String(255))
    status = db.Column(db.String(50), default='proposed')  # 'draft', 'proposed', 'approved', 'in_progress', 'revision_requested', 'completed', 'archived', 'rejected'
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    approved_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    approved_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    creator = db.relationship('User', foreign_keys=[created_by], backref='created_projects')
    approver = db.relationship('User', foreign_keys=[approved_by], backref='approved_projects')

    @property
    def tech_stack(self):
        return self.technology_stack

    @tech_stack.setter
    def tech_stack(self, val):
        self.technology_stack = val

    @property
    def category(self):
        return self.domain

    @category.setter
    def category(self, val):
        self.domain = val
