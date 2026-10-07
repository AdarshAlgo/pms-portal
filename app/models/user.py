from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db, bcrypt, login_manager

class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    role_name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    users = db.relationship('User', backref='role', lazy=True)

    def __repr__(self):
        return f'<Role {self.role_name}>'

    def __str__(self):
        return self.role_name

    def __eq__(self, other):
        if isinstance(other, str):
            return self.role_name.lower() == other.lower()
        if isinstance(other, Role):
            return self.id == other.id
        return False

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, index=True, nullable=False)
    email = db.Column(db.String(120), unique=True, index=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'), nullable=False)
    department = db.Column(db.String(100))
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=True)
    department_rel = db.relationship('Department', foreign_keys=[department_id], backref='affiliated_users')
    enrollment_number = db.Column(db.String(50), unique=True)
    is_verified = db.Column(db.Boolean, default=True)
    is_active = db.Column(db.Boolean, default=True)

    def __init__(self, **kwargs):
        if 'username' not in kwargs or not kwargs['username']:
            if 'email' in kwargs and kwargs['email']:
                kwargs['username'] = kwargs['email'].split('@')[0]
        if 'is_verified' not in kwargs:
            kwargs['is_verified'] = True
        super().__init__(**kwargs)

    # User Governance & Security Lifecycle States: 'active', 'inactive', 'suspended', 'blacklisted'
    status = db.Column(db.String(20), default='active')
    block_reason = db.Column(db.Text, nullable=True)
    blocked_at = db.Column(db.DateTime, nullable=True)
    blocked_by_admin_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    blocked_by_admin = db.relationship('User', remote_side=[id], foreign_keys=[blocked_by_admin_id], backref='blocked_users')

    can_evaluate = db.Column(db.Boolean, default=True)
    can_submit = db.Column(db.Boolean, default=True)
    permission_level = db.Column(db.String(50), default='full')  # 'full', 'standard', 'restricted'
    last_seen_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @property
    def is_blacklisted(self):
        return self.status == 'blacklisted'

    @property
    def is_inactive(self):
        return self.status == 'inactive'

    @property
    def is_suspended(self):
        return self.status == 'suspended'

    def set_password(self, password):
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')

    def check_password(self, password):
        if not self.password_hash:
            return False
        try:
            if check_password_hash(self.password_hash, password):
                return True
        except Exception:
            pass
        try:
            return bcrypt.check_password_hash(self.password_hash, password)
        except Exception:
            return False

    @property
    def has_password(self):
        return bool(self.password_hash)

    @property
    def full_name(self):
        if not self.last_name or not self.last_name.strip():
            return self.first_name.strip()
        return f"{self.first_name} {self.last_name}".strip()
        
    @property
    def is_admin(self):
        return self.role and self.role.role_name == 'admin'

    @property
    def is_faculty(self):
        return self.role and self.role.role_name == 'faculty'

    @property
    def is_student(self):
        return self.role and self.role.role_name == 'student'

    @property
    def is_online(self):
        if not self.last_seen_at:
            return False
        return (datetime.utcnow() - self.last_seen_at).total_seconds() < 900  # 15 minutes


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
