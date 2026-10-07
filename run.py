import os
from app import create_app
from app.extensions import db
from app.models.user import User, Role

app = create_app(os.environ.get('FLASK_ENV', 'development'))

# Ensure database tables exist upon application initialization (for Gunicorn & local)
with app.app_context():
    db.create_all()
    try:
        if not User.query.first():
            from seed import seed_database
            seed_database()
    except Exception:
        pass

@app.cli.command("init-db")
def init_db():
    """Initialize the database and create tables."""
    with app.app_context():
        db.create_all()
        print("Database tables created successfully.")

@app.cli.command("create-admin")
def create_admin():
    """Create a default admin user."""
    with app.app_context():
        admin_role = Role.query.filter_by(role_name='admin').first()
        if not admin_role:
            admin_role = Role(role_name='admin', description='System Administrator')
            db.session.add(admin_role)
            db.session.commit()
            
        admin_user = User.query.filter_by(email='admin@system.local').first()
        if not admin_user:
            admin_user = User(
                username='admin',
                email='admin@system.local',
                first_name='System',
                last_name='Admin',
                role_id=admin_role.id,
                is_active=True
            )
            admin_user.set_password('admin123')
            db.session.add(admin_user)
            db.session.commit()
            print("Admin user created (admin@system.local / admin123).")
        else:
            print("Admin user already exists.")

@app.cli.command("seed-db")
def seed_db():
    """Seed the database with default roles, users, and capstone milestones."""
    from seed import seed_database
    seed_database()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    debug = os.environ.get('FLASK_DEBUG', 'false').lower() in ('true', '1')
    app.run(host='0.0.0.0', port=port, debug=debug)
