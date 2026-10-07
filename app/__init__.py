from flask import Flask, render_template
import os

from app.extensions import db, login_manager, bcrypt, mail
from app.config import config_by_name

def create_app(config_name='development'):
    """App factory function to create and configure the Flask application."""
    app = Flask(__name__)
    app.config.from_object(config_by_name[config_name])

    # Auto-create runtime directories on app bootstrap
    os.makedirs(app.instance_path, exist_ok=True)
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'submissions'), exist_ok=True)

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    bcrypt.init_app(app)
    mail.init_app(app)

    # Register Blueprints
    from app.routes.auth import auth_bp
    from app.routes.admin import admin_bp
    from app.routes.faculty import faculty_bp
    from app.routes.student import student_bp
    from app.routes.api import api_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(faculty_bp)
    app.register_blueprint(student_bp)
    app.register_blueprint(api_bp)

    # Error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404

    @app.errorhandler(403)
    def forbidden_error(error):
        return render_template('errors/403.html'), 403

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('errors/500.html'), 500

    @app.before_request
    def check_user_access_status():
        from flask_login import current_user, logout_user
        from flask import session, redirect, url_for, flash, request, jsonify
        from app.models.user import User
        from datetime import datetime

        # Exclude static assets
        if request.path.startswith('/static'):
            return

        if current_user.is_authenticated:
            # Refresh user directly from DB to prevent stale session exploits
            user = db.session.get(User, current_user.id)
            if not user or user.status == 'blacklisted':
                logout_user()
                session.clear()
                if request.path.startswith('/api/') or request.is_json:
                    return jsonify({'error': 'Access Denied: Account Blacklisted', 'status': 403}), 403
                flash("Your account has been blacklisted and locked by administration. Access denied.", "danger")
                return redirect(url_for('auth.login'))
            elif user.status in ['inactive', 'suspended']:
                logout_user()
                session.clear()
                if request.path.startswith('/api/') or request.is_json:
                    return jsonify({'error': 'Access Denied: Account Inactive', 'status': 403}), 403
                flash("Your account is currently inactive. Contact your department coordinator.", "warning")
                return redirect(url_for('auth.login'))
            else:
                try:
                    user.last_seen_at = datetime.utcnow()
                    db.session.commit()
                except Exception:
                    db.session.rollback()

    # Root route for Portal Selection & Landing Page
    @app.route('/')
    def index():
        from flask import redirect, url_for
        from flask_login import current_user
        if current_user.is_authenticated:
            if current_user.is_admin:
                return redirect(url_for('admin.dashboard'))
            elif current_user.is_faculty:
                return redirect(url_for('faculty.dashboard'))
            elif current_user.is_student:
                return redirect(url_for('student.dashboard'))
        from app.models.project import Project
        projects = Project.query.all()
        return render_template('index.html', projects=projects)

    # Stripe-Inspired Modern Showcase Experience Route
    @app.route('/stripe')
    @app.route('/stripe-experience')
    def stripe_experience():
        return render_template('stripe_experience.html')

    # Context processors
    @app.context_processor
    def inject_user_role():
        from flask_login import current_user
        if current_user.is_authenticated:
            return dict(
                is_admin=current_user.is_admin,
                is_faculty=current_user.is_faculty,
                is_student=current_user.is_student
            )
        return dict(is_admin=False, is_faculty=False, is_student=False)

    return app
