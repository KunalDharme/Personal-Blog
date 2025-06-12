from app import app, db
from admin.models import AdminUser
from werkzeug.security import generate_password_hash

with app.app_context():
    db.create_all()  # Create tables if they don't exist
    
    # Check if admin user already exists
    if not AdminUser.query.filter_by(username='admin').first():
        admin = AdminUser(username='admin', password_hash=generate_password_hash('admin123'))
        db.session.add(admin)
        db.session.commit()
        print("Admin user created with username: admin and password: admin123")
    else:
        print("Admin user already exists.")
