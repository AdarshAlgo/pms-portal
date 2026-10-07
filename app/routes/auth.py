import re
from flask import Blueprint, request, jsonify, redirect, url_for, render_template, flash, session
from flask_login import login_user, logout_user, login_required, current_user

from app.services.auth_service import (
    authenticate_user, 
    register_user, 
    complete_user_registration, 
    validate_password_strength
)
from app.models.user import User, Role
from app.models.project import Department
from app.extensions import db
from app.utils.helpers import log_audit_event

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

# --------------------------------------------------------------------------
# 1. Standard Production Login
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


@auth_bp.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    session.clear()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('index'))


# --------------------------------------------------------------------------
# 2. Direct Single-Step Account Registration
# --------------------------------------------------------------------------

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """
    Direct Single-Step User Registration.
    Creates user account directly with name, unique username, email, role, department, and password.
    Enforces uniqueness and medium-strong password policy.
    """
    target_role = request.args.get('role', 'student').lower().strip()
    departments = Department.get_ordered()

    if current_user.is_authenticated:
        if current_user.is_admin:
            return redirect(url_for('admin.dashboard'))
        elif current_user.is_faculty:
            return redirect(url_for('faculty.dashboard'))
        elif current_user.is_student:
            return redirect(url_for('student.dashboard'))
        return redirect(url_for('index'))

    if request.method == 'POST':
        is_json = request.is_json
        data = request.get_json(silent=True) if is_json else request.form

        first_name = (data.get('first_name') or '').strip()
        last_name = (data.get('last_name') or '').strip()
        username = (data.get('username') or '').strip().lower()
        email = (data.get('email') or '').strip().lower()
        role_name = (data.get('role') or data.get('role_name') or 'student').strip().lower()
        department_id = (data.get('department_id') or '').strip() or None
        password = (data.get('password') or '').strip()
        confirm_password = (data.get('confirm_password') or '').strip()
        enrollment_number = (data.get('enrollment_number') or '').strip() or None

        # 1. Validation: Required fields
        if not first_name or not last_name:
            msg = 'First name and last name are required.'
            if is_json:
                return jsonify({'success': False, 'message': msg}), 400
            flash(msg, 'danger')
            return render_template('auth/register.html', target_role=target_role, departments=departments), 400

        if not username:
            msg = 'Username is required.'
            if is_json:
                return jsonify({'success': False, 'message': msg}), 400
            flash(msg, 'danger')
            return render_template('auth/register.html', target_role=target_role, departments=departments), 400

        if not re.match(r'^[a-zA-Z0-9_.]+$', username):
            msg = 'Username may only contain letters, numbers, underscores, and dots.'
            if is_json:
                return jsonify({'success': False, 'message': msg}), 400
            flash(msg, 'danger')
            return render_template('auth/register.html', target_role=target_role, departments=departments), 400

        if len(username) < 3:
            msg = 'Username must be at least 3 characters long.'
            if is_json:
                return jsonify({'success': False, 'message': msg}), 400
            flash(msg, 'danger')
            return render_template('auth/register.html', target_role=target_role, departments=departments), 400

        if not email:
            msg = 'University email address is required.'
            if is_json:
                return jsonify({'success': False, 'message': msg}), 400
            flash(msg, 'danger')
            return render_template('auth/register.html', target_role=target_role, departments=departments), 400

        if not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', email):
            msg = 'Please provide a valid university email address.'
            if is_json:
                return jsonify({'success': False, 'message': msg}), 400
            flash(msg, 'danger')
            return render_template('auth/register.html', target_role=target_role, departments=departments), 400

        # 2. Role restriction: strictly student or faculty, reject admin
        if role_name not in ['student', 'faculty']:
            msg = 'Admin registration is strictly prohibited. Contact institutional administration.'
            if is_json:
                return jsonify({'success': False, 'message': msg}), 403
            flash(msg, 'danger')
            return render_template('auth/register.html', target_role=target_role, departments=departments), 403

        # 3. Password matching and medium-strong strength validation
        if not password:
            msg = 'Password is required.'
            if is_json:
                return jsonify({'success': False, 'message': msg}), 400
            flash(msg, 'danger')
            return render_template('auth/register.html', target_role=target_role, departments=departments), 400

        if password != confirm_password:
            msg = 'Passwords do not match. Please verify and re-enter.'
            if is_json:
                return jsonify({'success': False, 'message': msg}), 400
            flash(msg, 'danger')
            return render_template('auth/register.html', target_role=target_role, departments=departments), 400

        is_valid_pwd, pwd_err = validate_password_strength(password)
        if not is_valid_pwd:
            if is_json:
                return jsonify({'success': False, 'message': pwd_err}), 400
            flash(pwd_err, 'danger')
            return render_template('auth/register.html', target_role=target_role, departments=departments), 400

        # 4. Uniqueness validation
        if User.query.filter(db.func.lower(User.username) == username).first():
            msg = "This username is already taken. Please choose another."
            if is_json:
                return jsonify({'success': False, 'message': msg}), 400
            flash(msg, 'danger')
            return render_template('auth/register.html', target_role=target_role, departments=departments), 400

        if User.query.filter(db.func.lower(User.email) == email).first():
            msg = 'An account with this email address already exists. Please sign in.'
            if is_json:
                return jsonify({'success': False, 'message': msg}), 400
            flash(msg, 'danger')
            return render_template('auth/register.html', target_role=target_role, departments=departments), 400

        try:
            user = register_user(
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                role_name=role_name,
                username=username,
                department_id=department_id,
                enrollment_number=enrollment_number
            )
            flash('Account created successfully! You can now log in.', 'success')
            if is_json:
                return jsonify({
                    'success': True,
                    'message': 'Account created successfully! You can now log in.',
                    'redirect_url': url_for('auth.login', role=role_name)
                }), 200
            return redirect(url_for('auth.login', role=role_name))
        except ValueError as e:
            if is_json:
                return jsonify({'success': False, 'message': str(e)}), 400
            flash(str(e), 'danger')
            return render_template('auth/register.html', target_role=target_role, departments=departments), 400

    return render_template('auth/register.html', target_role=target_role, departments=departments)


@auth_bp.route('/profile')
@login_required
def profile():
    return render_template('auth/login.html', user=current_user)
