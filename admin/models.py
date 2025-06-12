# admin/models.py
from extensions import db
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import re

class AdminUser(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class BlogPost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(200), unique=True, nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    likes = db.Column(db.Integer, default=0)
    
    # Relationship with comments
    comments = db.relationship('Comment', backref='blog', lazy=True, cascade='all, delete-orphan')

    def __init__(self, title, slug, content):
        self.title = title
        self.slug = slug if slug else self.generate_slug(title)
        self.content = content

    def generate_slug(self, title):
        # Generate URL-friendly slug from title
        slug = re.sub(r'[^\w\s-]', '', title.lower())
        slug = re.sub(r'[-\s]+', '-', slug)
        return slug.strip('-')

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    approved = db.Column(db.Boolean, default=False)
    
    # Foreign key to BlogPost
    blog_id = db.Column(db.Integer, db.ForeignKey('blog_post.id'), nullable=False)

    def __init__(self, name, text, blog_id, approved=False):
        self.name = name
        self.text = text
        self.blog_id = blog_id
        self.approved = approved

class ContactMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    read = db.Column(db.Boolean, default=False)

class Photo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

# NEW MODEL FOR SITE SETTINGS
class SiteSettings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    profile_image = db.Column(db.String(255), default='kunal.jpg')
    site_title = db.Column(db.String(200), default="Kunal's Blog")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @staticmethod
    def get_settings():
        """Get current site settings, create default if none exist"""
        settings = SiteSettings.query.first()
        if not settings:
            settings = SiteSettings()
            db.session.add(settings)
            db.session.commit()
        return settings