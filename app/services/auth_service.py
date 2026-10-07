import secrets
import hashlib
import hmac
from datetime import datetime, timedelta
import logging
from flask import current_app
from flask_mail import Message
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature

from app.extensions import db, mail
from app.models.user import User, Role, EmailVerification

logger = logging.getLogger(__name__)

# --------------------------------------------------------------------------
# 1. OTP Generation, Hashing & Verification
# --------------------------------------------------------------------------

def generate_otp() -> str:
    """Generates a secure 6-digit numeric OTP."""
    return f"{secrets.randbelow(900000) + 100000}"

def hash_otp(secret_key: str, otp: str) -> str:
    """Hashes the OTP using HMAC-SHA256 with the app secret key."""
    return hmac.new(secret_key.encode('utf-8'), otp.encode('utf-8'), hashlib.sha256).hexdigest()

def verify_otp_hash(secret_key: str, otp: str, stored_hash: str) -> bool:
    """Verifies the supplied OTP against the stored HMAC hash using constant-time comparison."""
    computed_hash = hash_otp(secret_key, otp)
    return hmac.compare_digest(computed_hash, stored_hash)

# --------------------------------------------------------------------------
# 2. Signed Registration Tokens (ItsDangerous)
# --------------------------------------------------------------------------

def generate_registration_token(email: str, secret_key: str) -> str:
    """Generates a signed temporary registration token valid for 15 minutes."""
    s = URLSafeTimedSerializer(secret_key)
    return s.dumps({'email': email, 'purpose': 'email_verification'})

def validate_registration_token(token: str, secret_key: str, max_age: int = 900):
    """Validates a signed registration token. Returns email if valid, or None."""
    s = URLSafeTimedSerializer(secret_key)
    try:
        data = s.loads(token, max_age=max_age)
        if data.get('purpose') == 'email_verification':
            return data.get('email')
    except (SignatureExpired, BadSignature, Exception):
        return None
    return None

# --------------------------------------------------------------------------
# 3. HTML Email Dispatch via Flask-Mail
# --------------------------------------------------------------------------

def send_otp_email(email: str, otp: str) -> bool:
    """Sends an official university branded HTML verification email with the 6-digit OTP."""
    subject = "Your Verification Code - PMS Portal"
    sender = current_app.config.get('MAIL_DEFAULT_SENDER', 'noreply@university.edu')
    
    # In development or testing mode when live credentials are not set, avoid outbound network latency
    if current_app.config.get('MAIL_SUPPRESS_SEND') or not current_app.config.get('MAIL_USERNAME'):
        logger.info(f"Suppressed external SMTP dispatch for {email} (credentials unconfigured or testing mode).")
        return True
    
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f8fafc; margin: 0; padding: 24px; color: #1e293b; }}
            .container {{ max-width: 520px; margin: 0 auto; background: #ffffff; border-radius: 16px; border: 1px solid #e2e8f0; overflow: hidden; box-shadow: 0 10px 30px rgba(0,0,0,0.05); }}
            .header {{ background: linear-gradient(135deg, #4f46e5, #7c3aed); padding: 32px 24px; text-align: center; color: #ffffff; }}
            .header h1 {{ margin: 0; font-size: 20px; font-weight: 800; letter-spacing: -0.02em; }}
            .header p {{ margin: 6px 0 0 0; font-size: 12px; opacity: 0.9; }}
            .content {{ padding: 32px 24px; text-align: center; }}
            .title {{ font-size: 18px; font-weight: 700; color: #0f172a; margin-bottom: 8px; }}
            .desc {{ font-size: 13px; color: #64748b; line-height: 1.6; margin-bottom: 24px; }}
            .otp-box {{ display: inline-block; background: #f1f5f9; border: 2px dashed #6366f1; border-radius: 12px; padding: 14px 28px; margin: 8px 0 24px 0; }}
            .otp-code {{ font-family: 'Courier New', Courier, monospace; font-size: 32px; font-weight: 900; letter-spacing: 8px; color: #4f46e5; margin: 0; }}
            .notice {{ font-size: 12px; color: #94a3b8; margin-top: 16px; line-height: 1.5; }}
            .footer {{ background: #f8fafc; border-top: 1px solid #e2e8f0; padding: 16px 24px; text-align: center; font-size: 11px; color: #94a3b8; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>PMS Academic Governance Portal</h1>
                <p>Project Progress Monitoring &amp; Evaluation System &bull; UN SDG 9</p>
            </div>
            <div class="content">
                <div class="title">Verify Your Email Address</div>
                <div class="desc">Please use the 6-digit verification code below to complete your registration. This code will expire in <strong>10 minutes</strong>.</div>
                <div class="otp-box">
                    <div class="otp-code">{otp}</div>
                </div>
                <div class="notice">
                    If you did not request this verification code, please ignore this email or notify your departmental administrator.
                </div>
            </div>
            <div class="footer">
                &copy; {datetime.utcnow().year} Project Progress Monitoring &amp; Evaluation System. All rights reserved.
            </div>
        </div>
    </body>
    </html>
    """
    
    text_body = f"Your PMS Portal Verification Code is: {otp}\n\nThis code will expire in 10 minutes.\nIf you did not request this code, please ignore this message."
    
    try:
        msg = Message(subject=subject, recipients=[email], html=html_body, body=text_body, sender=sender)
        mail.send(msg)
        logger.info(f"OTP verification email dispatched to {email}")
        return True
    except Exception as e:
        logger.warning(f"Failed to dispatch live SMTP email to {email}: {str(e)}")
        return False

# --------------------------------------------------------------------------
# 4. OTP Request & Verification Service
# --------------------------------------------------------------------------

def request_email_otp(email: str, secret_key: str) -> tuple[bool, str, str]:
    """
    Handles Step 1: Validates email, enforces rate limiting, generates OTP,
    hashes it, stores in database, and dispatches email.
    Returns (success, message, otp).
    """
    email = email.lower().strip()
    
    # 1. Check if user is already registered
    existing_user = User.query.filter_by(email=email).first()
    if existing_user and (existing_user.is_verified or existing_user.password_hash):
        return False, "An account with this email address is already registered. Please sign in.", ""
        
    # 2. Rate limiting defense: max 3 OTP requests in last 10 minutes
    ten_mins_ago = datetime.utcnow() - timedelta(minutes=10)
    recent_requests = EmailVerification.query.filter(
        EmailVerification.email == email,
        EmailVerification.created_at >= ten_mins_ago
    ).count()
    
    if recent_requests >= 3:
        return False, "Too many verification requests. Please wait 10 minutes before requesting a new code.", ""
        
    # 3. Generate and hash OTP
    otp = generate_otp()
    stored_hash = hash_otp(secret_key, otp)
    expires_at = datetime.utcnow() + timedelta(minutes=10)
    
    # Invalidate previous unused OTPs for this email
    EmailVerification.query.filter_by(email=email, is_used=False).update({'is_used': True})
    
    # 4. Save new verification record
    verification = EmailVerification(
        email=email,
        otp_hash=stored_hash,
        expires_at=expires_at,
        attempts=0,
        is_used=False
    )
    db.session.add(verification)
    db.session.commit()
    
    # 5. Send email
    send_otp_email(email, otp)
    
    return True, f"A 6-digit verification code has been sent to {email}.", otp

def verify_email_otp(email: str, otp: str, secret_key: str) -> tuple[bool, str, str]:
    """
    Handles Step 2: Validates OTP against database record, enforces 5 attempt limit,
    checks expiration, and generates a signed token.
    Returns (success, message, token).
    """
    email = email.lower().strip()
    otp = str(otp).strip()
    
    record = EmailVerification.query.filter_by(email=email, is_used=False)\
        .order_by(EmailVerification.created_at.desc()).first()
        
    if not record:
        return False, "No active verification request found. Please request a new code.", ""
        
    # Check max 5 attempts
    if record.attempts >= 5:
        record.is_used = True
        db.session.commit()
        return False, "Too many failed attempts. This code has been invalidated. Please request a new code.", ""
        
    # Check expiration
    if datetime.utcnow() > record.expires_at:
        record.is_used = True
        db.session.commit()
        return False, "Verification code has expired. Please request a new code.", ""
        
    # Check hash match
    if verify_otp_hash(secret_key, otp, record.otp_hash):
        record.is_used = True
        db.session.commit()
        token = generate_registration_token(email, secret_key)
        return True, "Email verified successfully!", token
    else:
        record.attempts += 1
        if record.attempts >= 5:
            record.is_used = True
            db.session.commit()
            return False, "Too many failed attempts. This code has been invalidated. Please request a new code.", ""
        db.session.commit()
        remaining = 5 - record.attempts
        return False, f"Invalid verification code. {remaining} attempt(s) remaining.", ""

# --------------------------------------------------------------------------
# 5. Account Registration Completion
# --------------------------------------------------------------------------

def complete_user_registration(email: str, password: str, first_name: str, last_name: str, 
                               role_name: str, department: str = None, enrollment_number: str = None,
                               username: str = None) -> User:
    """
    Handles Step 3: Enforces role safety (no admin registration), creates or updates
    user, sets non-nullable password hash, and marks account verified.
    """
    email = email.lower().strip()
    role_name = role_name.lower().strip()
    
    # Role safety defense: regular users cannot register themselves as admin
    if role_name not in ['student', 'faculty']:
        raise ValueError("Invalid role selected. Direct registration is only permitted for Student or Faculty roles.")
        
    role = Role.query.filter_by(role_name=role_name).first()
    if not role:
        raise ValueError(f"Role '{role_name}' does not exist in system.")
        
    if not password or len(password) < 8:
        raise ValueError("Password must be at least 8 characters long.")
        
    # Determine and validate unique username
    if username and username.strip():
        chosen_username = username.strip().lower()
    else:
        chosen_username = email.split('@')[0].lower()

    # Check if an existing unverified placeholder user exists
    user = User.query.filter_by(email=email).first()
    if user:
        if user.is_verified:
            raise ValueError("An account with this email address already exists.")
        
        # Verify username uniqueness if changed
        conflict = User.query.filter(
            db.func.lower(User.username) == chosen_username,
            User.id != user.id
        ).first()
        if conflict:
            chosen_username = f"{chosen_username}_{secrets.randbelow(1000)}"

        # Update existing unverified user
        user.username = chosen_username
        user.first_name = first_name.strip()
        user.last_name = last_name.strip()
        user.role_id = role.id
        user.department = department.strip() if department else None
        user.enrollment_number = enrollment_number.strip() if enrollment_number else None
        user.is_verified = True
        user.set_password(password)
    else:
        # Check if username is already taken by another user
        conflict = User.query.filter(db.func.lower(User.username) == chosen_username).first()
        if conflict:
            if username and username.strip():
                raise ValueError("This username is already taken. Please choose another.")
            chosen_username = f"{chosen_username}_{secrets.randbelow(1000)}"

        # Create brand new user with non-nullable password hash
        user = User(
            username=chosen_username,
            email=email,
            first_name=first_name.strip(),
            last_name=last_name.strip(),
            role_id=role.id,
            department=department.strip() if department else None,
            enrollment_number=enrollment_number.strip() if enrollment_number else None,
            is_verified=True,
            is_active=True
        )
        user.set_password(password)
        db.session.add(user)
        
    db.session.commit()
    return user

# --------------------------------------------------------------------------
# 6. Legacy / Direct Authenticate & Register Helpers
# --------------------------------------------------------------------------

def register_user(email: str, password: str, first_name: str, last_name: str, 
                  role_name: str, department: str = None, enrollment_number: str = None,
                  username: str = None) -> User:
    """Helper for direct registration (maintains backwards compatibility)."""
    return complete_user_registration(
        email=email,
        password=password,
        first_name=first_name,
        last_name=last_name,
        role_name=role_name,
        department=department,
        enrollment_number=enrollment_number,
        username=username
    )

def authenticate_user(identifier: str, password: str) -> User | None:
    """
    Authenticates user by username or email and password.
    Supports pure username login or email login interchangeably.
    """
    if not identifier or not password:
        return None
    clean_id = identifier.strip().lower()
    user = User.query.filter(
        db.or_(
            db.func.lower(User.username) == clean_id,
            db.func.lower(User.email) == clean_id
        )
    ).first()
    if user and user.check_password(password) and user.is_active:
        return user
    return None

def change_password(user: User, old_password: str, new_password: str) -> bool:
    """Changes user password after checking old password."""
    if not user.check_password(old_password):
        return False
    user.set_password(new_password)
    db.session.commit()
    return True
