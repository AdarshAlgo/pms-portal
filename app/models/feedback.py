import json
from datetime import datetime
from app.extensions import db

class FeedbackLog(db.Model):
    __tablename__ = 'feedback_logs'
    id = db.Column(db.Integer, primary_key=True)
    submission_id = db.Column(db.Integer, db.ForeignKey('submissions.id'), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    feedback_type = db.Column(db.String(50))  # approval, revision_request, advisory_note, admin_intervention, comment, rejection
    content = db.Column(db.Text, nullable=False)
    is_private = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    author = db.relationship('User', foreign_keys=[author_id], backref='authored_feedback')
    submission = db.relationship('Submission', backref=db.backref('feedback_entries', lazy=True, cascade='all, delete-orphan'))

    @property
    def timestamp(self):
        return self.created_at

class MeetingLog(db.Model):
    __tablename__ = 'meeting_logs'
    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey('teams.id'), nullable=False)
    scheduled_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    meeting_date = db.Column(db.DateTime, nullable=False)
    duration_minutes = db.Column(db.Integer, default=30)
    agenda = db.Column(db.Text)
    minutes = db.Column(db.Text)
    attendees_count = db.Column(db.Integer, default=1)
    status = db.Column(db.String(50), default='scheduled')  # scheduled, completed, cancelled
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    team = db.relationship('Team', backref='meeting_logs')
    scheduler = db.relationship('User', foreign_keys=[scheduled_by])

class Notification(db.Model):
    __tablename__ = 'notifications'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(150), nullable=False)
    message = db.Column(db.Text, nullable=False)
    notification_type = db.Column(db.String(50))  # submission, feedback, warning, deadline, admin
    is_read = db.Column(db.Boolean, default=False)
    related_entity_type = db.Column(db.String(50))  # 'submission', 'meeting', 'project', 'team'
    related_entity_id = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='notifications')

class AuditLog(db.Model):
    __tablename__ = 'audit_logs'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    action = db.Column(db.String(150), nullable=False)
    entity_type = db.Column(db.String(50))
    entity_id = db.Column(db.Integer)
    details = db.Column(db.Text)  # JSON or text description
    ip_address = db.Column(db.String(50), default='127.0.0.1')
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='audit_logs')

    @property
    def created_at(self):
        return self.timestamp

    @property
    def parsed_details(self):
        if not self.details:
            return {}
        try:
            return json.loads(self.details)
        except Exception:
            return {'text': self.details}

# Retain ActivityLog for backwards-compatibility
class ActivityLog(db.Model):
    __tablename__ = 'activity_logs'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    action = db.Column(db.String(255), nullable=False)
    entity_type = db.Column(db.String(50))
    entity_id = db.Column(db.Integer)
    details = db.Column(db.Text)
    ip_address = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='activity_logs')

class SystemSetting(db.Model):
    __tablename__ = 'system_settings'
    id = db.Column(db.Integer, primary_key=True)
    setting_key = db.Column(db.String(100), unique=True, nullable=False)
    setting_value = db.Column(db.Text, nullable=False)
    description = db.Column(db.String(255))
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @classmethod
    def get(cls, key, default=None):
        setting = cls.query.filter_by(setting_key=key).first()
        return setting.setting_value if setting else default

    @classmethod
    def set(cls, key, value, description=None):
        setting = cls.query.filter_by(setting_key=key).first()
        if not setting:
            setting = cls(setting_key=key, setting_value=str(value), description=description)
            db.session.add(setting)
        else:
            setting.setting_value = str(value)
            if description:
                setting.description = description
        db.session.commit()
        return setting
