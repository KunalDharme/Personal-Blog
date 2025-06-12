# create_db.py
from app import app, db
from admin.models import AdminUser, BlogPost, Comment, ContactMessage, Photo, SiteSettings

def initialize_database():
    with app.app_context():
        db.drop_all()  # Drop all tables (optional, for full reset)
        db.create_all()
        print("✅ Fresh database created.")

        # Create default admin user
        if not AdminUser.query.filter_by(username='admin').first():
            admin = AdminUser(username='admin')
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            print("🛡️ Default admin 'admin' created with password 'admin123'.")

        # Create default site settings
        if not SiteSettings.query.first():
            settings = SiteSettings()
            db.session.add(settings)
            db.session.commit()
            print("⚙️ Default site settings created.")

if __name__ == "__main__":
    initialize_database()