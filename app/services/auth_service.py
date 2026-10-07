import re
import logging
from datetime import datetime
from flask import current_app

from app.extensions import db
from app.models.user import User, Role
from app.models.project import Department

logger = logging.getLogger(__name__)

# --------------------------------------------------------------------------
# Password Validation & Security Policies
# --------------------------------------------------------------------------

def validate_password_strength(password: str) -> tuple[bool, str]:
    """
    Validates that a password satisfies the medium-strong institutional policy:
    - Minimum 8 characters
    - At least 1 letter
    - At least 1 number
    - At least 1 special character / symbol
    """
    if not password or len(password) < 8:
        return False, "Password must be at least 8 characters long."
    if not re.search(r'[A-Za-z]', password):
        return False, "Password must contain at least one letter."
    if not re.search(r'\d', password):
        return False, "Password must contain at least one number."
    if not re.search(r'[!@#$%^&*(),.?":{}|<>_~`\-+=\[\]\\;\'/]', password):
        return False, "Password must contain at least one special character or symbol."
    return True, ""


# --------------------------------------------------------------------------
# Direct Account Registration & Authentication Service
# --------------------------------------------------------------------------

def register_user(
    email: str,
    password: str,
    first_name: str,
    last_name: str,
    role_name: str,
    username: str = None,
    department_id: int | str = None,
    department: str = None,
    enrollment_number: str = None
) -> User:
    """
    Direct single-step user registration.
    Enforces role safety (no admin registration), validates uniqueness of username and email,
    enforces medium-strong password policy, initializes user with is_verified=True, and commits to DB.
    """
    if not email or not email.strip():
        raise ValueError("Email address is required.")
    email = email.lower().strip()
    
    # Email format validation
    if not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', email):
        raise ValueError("Please provide a valid university email address.")

    if not first_name or not first_name.strip():
        raise ValueError("First name is required.")
    if not last_name or not last_name.strip():
        raise ValueError("Last name is required.")

    # Medium-strong password policy check
    is_valid_pwd, pwd_err = validate_password_strength(password)
    if not is_valid_pwd:
        raise ValueError(pwd_err)

    role_name = (role_name or 'student').lower().strip()
    if role_name not in ['student', 'faculty']:
        raise ValueError("Invalid role selected. Direct registration is only permitted for Student or Faculty roles.")

    role = Role.query.filter_by(role_name=role_name).first()
    if not role:
        raise ValueError(f"System role '{role_name}' does not exist.")

    # Username handling & validation
    if username and username.strip():
        chosen_username = username.strip().lower()
    else:
        chosen_username = email.split('@')[0].lower()

    if not re.match(r'^[a-zA-Z0-9_.]+$', chosen_username):
        raise ValueError("Username may only contain letters, numbers, underscores, and dots.")

    if len(chosen_username) < 3:
        raise ValueError("Username must be at least 3 characters long.")

    # Check for username conflict (clean exact message)
    existing_username = User.query.filter(db.func.lower(User.username) == chosen_username).first()
    if existing_username:
        raise ValueError("This username is already taken. Please choose another.")

    # Check for email conflict
    existing_email = User.query.filter(db.func.lower(User.email) == email).first()
    if existing_email:
        raise ValueError("An account with this email address already exists. Please sign in.")

    # Department resolution
    dept_id = None
    dept_name = None
    if department_id:
        try:
            dept_id_int = int(department_id)
            dept_obj = Department.query.get(dept_id_int)
            if dept_obj:
                dept_id = dept_obj.id
                dept_name = dept_obj.name
        except (ValueError, TypeError):
            pass

    if not dept_name and department and department.strip():
        dept_str = department.strip()
        dept_obj = Department.query.filter(
            db.or_(
                db.func.lower(Department.name) == dept_str.lower(),
                db.func.lower(Department.code) == dept_str.lower()
            )
        ).first()
        if dept_obj:
            dept_id = dept_obj.id
            dept_name = dept_obj.name
        else:
            dept_name = dept_str

    user = User(
        username=chosen_username,
        email=email,
        first_name=first_name.strip(),
        last_name=last_name.strip(),
        role_id=role.id,
        department=dept_name,
        department_id=dept_id,
        enrollment_number=enrollment_number.strip() if enrollment_number else None,
        is_verified=True,
        is_active=True,
        status='active'
    )
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    logger.info(f"User {user.username} ({user.email}) registered successfully as {role_name}.")
    return user

# Backward-compatible alias
complete_user_registration = register_user

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
