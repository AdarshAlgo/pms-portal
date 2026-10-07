import os
import json
import uuid
from datetime import datetime
from werkzeug.utils import secure_filename
from flask import current_app, request
from app.extensions import db
from app.models.feedback import AuditLog, ActivityLog

ALLOWED_EXTENSIONS = {'pdf', 'zip', 'docx', 'doc', 'tar.gz', 'pptx'}

def format_datetime(value, format="%Y-%m-%d %H:%M"):
    """Format a datetime object."""
    if value is None:
        return ""
    return value.strftime(format)

def allowed_file(filename):
    """Check if uploaded file has allowed extension."""
    if '.' not in filename:
        return False
    ext = filename.rsplit('.', 1)[1].lower()
    return ext in ALLOWED_EXTENSIONS

def save_uploaded_file(file_storage, subfolder='submissions'):
    """Securely save uploaded file and return relative static URL."""
    if not file_storage or not file_storage.filename:
        return None
    
    filename = secure_filename(file_storage.filename)
    if not filename or not allowed_file(filename):
        return None
        
    ext = filename.rsplit('.', 1)[1].lower()
    unique_name = f"{uuid.uuid4().hex[:12]}_{int(datetime.utcnow().timestamp())}.{ext}"
    
    upload_dir = os.path.join(current_app.config.get('UPLOAD_FOLDER', 'app/static/uploads'), subfolder)
    os.makedirs(upload_dir, exist_ok=True)
    
    file_path = os.path.join(upload_dir, unique_name)
    file_storage.save(file_path)
    
    return f"/static/uploads/{subfolder}/{unique_name}"

def log_audit_event(user_id, action, entity_type=None, entity_id=None, details=None, ip_address=None):
    """Persist an immutable audit trail entry across both AuditLog and ActivityLog tables."""
    try:
        ip = ip_address or (request.remote_addr if request else '127.0.0.1')
    except Exception:
        ip = '127.0.0.1'

    details_str = json.dumps(details) if isinstance(details, (dict, list)) else (str(details) if details else '')
    
    audit = AuditLog(
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        details=details_str,
        ip_address=ip,
        timestamp=datetime.utcnow()
    )
    db.session.add(audit)

    # Backwards compatibility with ActivityLog
    activity = ActivityLog(
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        details=details_str,
        ip_address=ip,
        created_at=datetime.utcnow()
    )
    db.session.add(activity)
    
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
