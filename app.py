from flask import Flask, render_template, redirect, url_for, request, session, flash, jsonify
from extensions import db
from werkzeug.utils import secure_filename
from datetime import datetime
import os

# Import config and models
from config import Config
from admin.models import ContactMessage, BlogPost, Comment

# Initialize Flask app and config
app = Flask(__name__)
app.config.from_object(Config)

# Upload folder configuration
UPLOAD_FOLDER = os.path.join('static', 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Initialize database
db.init_app(app)
with app.app_context():
    db.create_all()

# Register admin blueprint
from admin.routes import admin_routes
app.register_blueprint(admin_routes, url_prefix='/admin')

# ------------------ Public Routes ------------------

# Replace your existing home() function in app.py with this:

@app.route('/')
@app.route('/index.html')
def home():
    """Homepage showing recent blogs and photo previews"""
    recent_blogs = BlogPost.query.order_by(BlogPost.created_at.desc()).limit(3).all()
    
    # Get famous blogs (those with most likes)
    famous_blogs = BlogPost.query.order_by(BlogPost.likes.desc()).limit(5).all()

    # Get the list of photo filenames from the upload folder
    uploads_folder = os.path.join(app.static_folder, 'uploads')
    if os.path.exists(uploads_folder):
        photo_list = sorted(os.listdir(uploads_folder), reverse=True)[:4]  # Show latest 4
    else:
        photo_list = []

    # Get current profile image from site settings
    from admin.models import SiteSettings
    settings = SiteSettings.get_settings()
    
    return render_template('index.html', 
                         blogs=recent_blogs, 
                         photo_list=photo_list, 
                         famous_blogs=famous_blogs,
                         profile_image=settings.profile_image)

@app.route('/blog.html')
def all_blogs():
    """All blog posts"""
    all_blogs = BlogPost.query.order_by(BlogPost.created_at.desc()).all()
    return render_template('blog.html', blogs=all_blogs)

@app.route('/blog/<int:blog_id>')
def blog_detail(blog_id):
    """Fallback blog detail page if needed (uses dummy data)"""
    # Optional: could remove if not using dummy blogs
    return redirect(url_for('all_blogs'))

@app.route('/add_comment/<slug>', methods=['POST'])
def add_comment(slug):
    """Add a comment to a blog post"""
    try:
        post = BlogPost.query.filter_by(slug=slug).first_or_404()
        name = request.form.get('name', '').strip()
        text = request.form.get('text', '').strip()
        
        if not name or not text:
            return jsonify({'success': False, 'error': 'Name and comment text are required'}), 400
        
        # Create comment (not approved by default)
        comment = Comment(name=name, text=text, blog_id=post.id, approved=False)
        db.session.add(comment)
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'name': name, 
            'text': text,
            'message': 'Comment submitted for approval'
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/like_post/<slug>', methods=['POST'])
def like_post(slug):
    """Handle post likes"""
    try:
        post = BlogPost.query.filter_by(slug=slug).first_or_404()
        
        # Get the action (like or unlike)
        action = request.json.get('action', 'like')
        
        if action == 'like':
            post.likes = (post.likes or 0) + 1
        elif action == 'unlike' and post.likes > 0:
            post.likes = post.likes - 1
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'likes': post.likes,
            'action': action
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/get_post_data/<slug>')
def get_post_data(slug):
    """Get post data including likes and comments"""
    try:
        post = BlogPost.query.filter_by(slug=slug).first_or_404()
        
        # Get approved comments
        approved_comments = Comment.query.filter_by(
            blog_id=post.id, 
            approved=True
        ).order_by(Comment.created_at.desc()).all()
        
        comments_data = [{
            'name': comment.name,
            'text': comment.text,
            'created_at': comment.created_at.strftime('%B %d, %Y at %I:%M %p')
        } for comment in approved_comments]
        
        return jsonify({
            'success': True,
            'likes': post.likes or 0,
            'comments': comments_data
        })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/photos.html', methods=['GET', 'POST'])
def photos():
    """Photo upload and display page"""
    if request.method == 'POST':
        if 'photo' in request.files:
            file = request.files['photo']
            if file and file.filename.endswith(('.png', '.jpg', '.jpeg', '.gif')):
                filename = secure_filename(file.filename)
                os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                flash('Photo uploaded successfully!', 'success')
                return redirect(url_for('photos'))
            else:
                flash('Invalid file type.', 'danger')

    if os.path.exists(app.config['UPLOAD_FOLDER']):
        uploaded_photos = os.listdir(app.config['UPLOAD_FOLDER'])
        uploaded_photos = [f for f in uploaded_photos if f.endswith(('.png', '.jpg', '.jpeg', '.gif'))]
    else:
        uploaded_photos = []
    
    return render_template('photos.html', photo_list=uploaded_photos)

@app.route('/contact.html', methods=['GET', 'POST'])
def contact():
    """Contact form handling with basic validation"""
    from admin.models import SiteSettings
    settings = SiteSettings.get_settings()

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        message = request.form.get('message', '').strip()

        if not name or not email or not message:
            flash('Please fill out all fields.', 'contact')
            return redirect(url_for('contact'))

        contact_message = ContactMessage(name=name, email=email, message=message)
        db.session.add(contact_message)
        db.session.commit()

        flash('Your message has been sent successfully!', 'contact')
        return redirect(url_for('contact'))

    return render_template('contact.html', profile_image=settings.profile_image)

@app.route('/help.html')
def help():
    """help"""
    return render_template('help.html')

# ------------------ Blog Detail + Comments ------------------

@app.route('/post/<slug>', methods=['GET', 'POST'])
def post(slug):
    """Detailed blog post view with comments"""
    post = BlogPost.query.filter_by(slug=slug).first_or_404()

    if request.method == 'POST':
        name = request.form['name']
        text = request.form['text']
        comment = Comment(name=name, text=text, blog_id=post.id, approved=False)
        db.session.add(comment)
        db.session.commit()
        flash('Comment submitted for approval!', 'success')
        return redirect(url_for('post', slug=slug))  # PRG pattern

    # Get approved comments
    comments = Comment.query.filter_by(blog_id=post.id, approved=True).order_by(Comment.created_at.desc()).all()
    return render_template('post.html', post=post, comments=comments)

# ------------------ Admin Access Shortcut ------------------

@app.route("/admin/templates/admin/admin.html")
def admin_panel():
    """Shortcut route to admin panel (optional)"""
    return render_template("admin.html")

# ------------------ Run App ------------------

if __name__ == '__main__':
    app.run(debug=True)