from flask import Blueprint, request, jsonify, redirect, url_for, render_template, flash, session, current_app
from flask_login import login_user, logout_user, login_required, current_user
import re

from app.services.auth_service import (
    authenticate_user, 
    register_user, 
    request_email_otp, 
    verify_email_otp,
    complete_user_registration,
    validate_registration_token
)
from app.models.user import User, Role
from app.models.project import Department
from app.extensions import db
from app.utils.helpers import log_audit_event

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

# --------------------------------------------------------------------------
# 1. Standard Login & 1-Click Quick Demo Login
# --------------------------------------------------------------------------

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    Standard Username / Email + Password Login Route.
    Validates credentials, checks account status, logs in via Flask-Login,
    and redirects user to their role-specific dashboard.
    """
    target_role = request.args.get('role', '').lower().strip()
    
    if current_user.is_authenticated:
        if current_user.is_admin:
            return redirect(url_for('admin.dashboard'))
        elif current_user.is_faculty:
            return redirect(url_for('faculty.dashboard'))
        elif current_user.is_student:
            return redirect(url_for('student.dashboard'))
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        # Accept username or email from login input
        identifier = (request.form.get('username') or request.form.get('email') or request.form.get('login_id') or '').strip()
        password = request.form.get('password', '').strip()
        remember = bool(request.form.get('remember_me') or request.form.get('remember'))
        
        user = authenticate_user(identifier, password)
        if user:
            # Prevent session creation for blacklisted or inactive accounts
            if getattr(user, 'status', 'active') == 'blacklisted':
                log_audit_event(
                    user_id=user.id,
                    action='blacklisted_login_blocked',
                    entity_type='user',
                    entity_id=user.id,
                    details={'email': user.email, 'username': user.username, 'reason': getattr(user, 'block_reason', 'Account Blacklisted')}
                )
                flash('Account Locked: Your profile has been permanently blacklisted by institutional administration. Access denied.', 'danger')
                return render_template('auth/login.html', target_role=target_role), 403
            elif getattr(user, 'status', 'active') in ('inactive', 'suspended') or not user.is_active:
                flash('Account Inactive: Your account is currently paused or inactive. Please contact your department coordinator.', 'warning')
                return render_template('auth/login.html', target_role=target_role)

            login_user(user, remember=remember)
            flash(f'Welcome back, {user.first_name}!', 'success')
            
            # Check for safe next redirect
            next_page = request.args.get('next')
            if next_page and not next_page.startswith('/auth') and not next_page.startswith('//'):
                return redirect(next_page)

            # Redirect based on user role
            if user.is_admin:
                return redirect(url_for('admin.dashboard'))
            elif user.is_faculty:
                return redirect(url_for('faculty.dashboard'))
            elif user.is_student:
                return redirect(url_for('student.dashboard'))
            return redirect(url_for('index'))
        else:
            flash('Invalid username/email or password. Please try again.', 'danger')
            
    return render_template('auth/login.html', target_role=target_role)

@auth_bp.route('/quick-login/<role>')
def quick_login(role):
    """1-Click quick login for demo, institutional evaluations, and grading verification."""
    role = role.lower().strip()
    email_map = {
        'admin': 'admin@university.edu',
        'admin1': 'admin@university.edu',
        'faculty': 'dr.verma@university.edu',
        'faculty1': 'dr.verma@university.edu',
        'student': 'student1@university.edu',
        'student1': 'student1@university.edu'
    }
    
    email = email_map.get(role)
    if not email:
        flash('Invalid role specified.', 'danger')
        return redirect(url_for('auth.login'))
        
    user = User.query.filter_by(email=email).first()
    if user:
        if getattr(user, 'status', 'active') == 'blacklisted':
            flash('Account Locked: This account has been blacklisted.', 'danger')
            return redirect(url_for('auth.login'))
        elif getattr(user, 'status', 'active') in ('inactive', 'suspended'):
            flash('Account Inactive: This account is currently inactive.', 'warning')
            return redirect(url_for('auth.login'))

        login_user(user)
        flash(f'Logged in via 1-Click Demo as {user.full_name} ({user.role.role_name.capitalize()})', 'info')
        if user.is_admin:
            return redirect(url_for('admin.dashboard'))
        elif user.is_faculty:
            return redirect(url_for('faculty.dashboard'))
        elif user.is_student:
            return redirect(url_for('student.dashboard'))
    else:
        flash('Default user not found. Please register or seed database.', 'warning')
        
    return redirect(url_for('auth.login'))

@auth_bp.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    session.clear()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('index'))

# --------------------------------------------------------------------------
# 3. Email Registration with Real-Time 6-Digit OTP Verification Flow
# --------------------------------------------------------------------------

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Renders multi-step registration UI or processes direct registration."""
    target_role = request.args.get('role', 'student').lower().strip()
    departments = Department.query.all()
    
    # Backwards compatibility: If a complete POST form is submitted directly
    if request.method == 'POST':
        try:
            role_name = request.form.get('role_name') or request.form.get('role') or 'student'
            email = request.form.get('email', '').strip()
            username = request.form.get('username', '').strip() or None
            password = request.form.get('password', '').strip()
            first_name = request.form.get('first_name', '').strip()
            last_name = request.form.get('last_name', '').strip()
            department = request.form.get('department', '').strip()
            enrollment_number = request.form.get('enrollment_number', '').strip() or None
            
            user = complete_user_registration(
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                role_name=role_name,
                department=department,
                enrollment_number=enrollment_number,
                username=username
            )
            flash(f'Account created successfully as {role_name.capitalize()}! Please sign in.', 'success')
            return redirect(url_for('auth.login', role=role_name))
        except ValueError as e:
            flash(str(e), 'danger')
            
    return render_template('auth/register.html', target_role=target_role, departments=departments)

@auth_bp.route('/register/request-otp', methods=['POST'])
def request_otp():
    """
    Step 1: Request 6-digit numeric OTP for email registration.
    Validates format, checks for existing accounts, enforces rate limiting, and dispatches email.
    """
    data = request.get_json(silent=True) or request.form
    email = data.get('email', '').strip()
    
    if not email:
        return jsonify({'success': False, 'message': 'Email address is required.'}), 400
        
    # Basic email format validation
    email_regex = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    if not re.match(email_regex, email):
        return jsonify({'success': False, 'message': 'Please enter a valid university email address.'}), 400
        
    secret_key = current_app.config['SECRET_KEY']
    success, message, _ = request_email_otp(email, secret_key)
    
    if not success:
        status_code = 429 if 'Too many' in message else 400
        return jsonify({'success': False, 'message': message}), status_code
        
    return jsonify({
        'success': True,
        'message': message
    }), 200

@auth_bp.route('/register/verify-otp', methods=['POST'])
def verify_otp():
    """
    Step 2: Verify submitted 6-digit OTP.
    Enforces 5 attempt limit and 10-minute expiration. Returns signed verification token.
    """
    data = request.get_json(silent=True) or request.form
    email = data.get('email', '').strip()
    otp = data.get('otp', '').strip()
    
    if not email or not otp:
        return jsonify({'success': False, 'message': 'Both email and verification code are required.'}), 400
        
    secret_key = current_app.config['SECRET_KEY']
    success, message, token = verify_email_otp(email, otp, secret_key)
    
    if not success:
        return jsonify({'success': False, 'message': message}), 400
        
    # Store verified email & token in session
    session['verified_registration_email'] = email
    session['verified_registration_token'] = token
    
    return jsonify({
        'success': True,
        'message': message,
        'token': token
    }), 200

@auth_bp.route('/register/complete', methods=['POST'])
def complete_registration():
    """
    Step 3: Complete Account Setup.
    Requires validated verification token, sets password, first/last name, role and department.
    """
    data = request.get_json(silent=True) or request.form
    
    token = data.get('token') or session.get('verified_registration_token')
    email = data.get('email') or session.get('verified_registration_email')
    
    if not token or not email:
        return jsonify({'success': False, 'message': 'Missing email verification. Please verify your email first.'}), 400
        
    # Validate token signature and expiration
    secret_key = current_app.config['SECRET_KEY']
    token_email = validate_registration_token(token, secret_key)
    if not token_email or token_email.lower() != email.lower().strip():
        return jsonify({'success': False, 'message': 'Verification token has expired or is invalid. Please request a new code.'}), 400
        
    first_name = data.get('first_name', '').strip()
    last_name = data.get('last_name', '').strip()
    password = data.get('password', '').strip()
    confirm_password = data.get('confirm_password', '').strip()
    role_name = (data.get('role_name') or data.get('role') or 'student').lower().strip()
    department = data.get('department', '').strip()
    enrollment_number = data.get('enrollment_number', '').strip() or None
    
    if not first_name or not last_name:
        return jsonify({'success': False, 'message': 'First name and last name are required.'}), 400
        
    if not password:
        return jsonify({'success': False, 'message': 'Password is required.'}), 400
        
    if password != confirm_password:
        return jsonify({'success': False, 'message': 'Passwords do not match.'}), 400
        
    if len(password) < 8:
        return jsonify({'success': False, 'message': 'Password must be at least 8 characters long.'}), 400
        
    username = data.get('username', '').strip() or None
    
    # Role safety defense
    if role_name not in ['student', 'faculty']:
        return jsonify({'success': False, 'message': 'Registration as Admin is restricted. Contact university coordinator.'}), 403
        
    try:
        user = complete_user_registration(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            role_name=role_name,
            department=department,
            enrollment_number=enrollment_number,
            username=username
        )
        
        # Log user in immediately
        login_user(user)
        
        # Clear verification session keys
        session.pop('verified_registration_email', None)
        session.pop('verified_registration_token', None)
        
        redirect_url = url_for('student.dashboard' if user.is_student else 'faculty.dashboard')
        
        return jsonify({
            'success': True,
            'message': f'Account successfully created as {role_name.capitalize()}! Welcome, {user.first_name}.',
            'redirect_url': redirect_url
        }), 200
    except ValueError as e:
        return jsonify({'success': False, 'message': str(e)}), 400

@auth_bp.route('/profile')
@login_required
def profile():
    return render_template('auth/login.html', user=current_user)
