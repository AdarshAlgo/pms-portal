from functools import wraps
from flask import abort, request
from flask_login import current_user
from app.extensions import db
from app.models.feedback import ActivityLog

def role_required(*roles):
    """Decorator to check if user has required role."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return abort(401)
            if getattr(current_user, 'status', 'active') in ('blacklisted', 'inactive', 'suspended'):
                return abort(403)
            if not current_user.role or current_user.role.role_name not in roles:
                return abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def admin_required(f):
    """Shortcut for admin role requirement."""
    return role_required('admin')(f)

def faculty_required(f):
    """Shortcut for faculty role requirement."""
    return role_required('faculty', 'admin')(f)

def student_required(f):
    """Shortcut for student role requirement."""
    return role_required('student')(f)

def log_activity(action):
    """Decorator to log user actions."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if current_user.is_authenticated:
                log = ActivityLog(
                    user_id=current_user.id,
                    action=action,
                    ip_address=request.remote_addr,
                    entity_type=request.endpoint
                )
                db.session.add(log)
                db.session.commit()
            return f(*args, **kwargs)
        return decorated_function
    return decorator
