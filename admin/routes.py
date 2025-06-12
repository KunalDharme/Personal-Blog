import os
from flask import Blueprint, render_template, redirect, url_for, request, session, flash, current_app
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from extensions import db 
from .models import AdminUser, BlogPost, Photo, ContactMessage, Comment, SiteSettings

admin_routes = Blueprint('admin', __name__, template_folder='templates')

UPLOAD_FOLDER = os.path.join(os.getcwd(), 'static', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def admin_login_required():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin.login'))
    return None

@admin_routes.route('/')
def admin_root():
    return redirect(url_for('admin.dashboard'))

@admin_routes.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = AdminUser.query.filter_by(username=username).first()

        if user and check_password_hash(user.password_hash, password):
            session['admin_logged_in'] = True
            session['admin_id'] = user.id
            return redirect(url_for('admin.dashboard'))
        else:
            flash('Invalid credentials', 'danger')

    return render_template('admin/login.html')

@admin_routes.route('/dashboard')
def dashboard():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin.login'))

    total_posts = BlogPost.query.count()
    recent_posts = BlogPost.query.order_by(BlogPost.created_at.desc()).limit(5).all()
    return render_template('admin/admin_dashboard.html', total_posts=total_posts, recent_posts=recent_posts)

@admin_routes.route('/logout')
def logout():
    session.pop('admin_logged_in', None)
    session.pop('admin_id', None)
    return redirect(url_for('admin.login'))

@admin_routes.route('/posts')
def posts():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin.login'))

    all_posts = BlogPost.query.order_by(BlogPost.created_at.desc()).all()
    return render_template('admin/admin_posts.html', posts=all_posts)

@admin_routes.route('/post/new', methods=['GET', 'POST'])
def new_post():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin.login'))

    if request.method == 'POST':
        title = request.form['title']
        slug = request.form['slug']
        content = request.form['content']

        post = BlogPost(title=title, slug=slug, content=content)
        db.session.add(post)
        db.session.commit()
        return redirect(url_for('admin.posts'))

    return render_template('admin/new_post.html')

@admin_routes.route('/post/edit/<int:blog_id>', methods=['GET', 'POST'])
def edit_post(blog_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin.login'))

    post = BlogPost.query.get_or_404(blog_id)

    if request.method == 'POST':
        post.title = request.form['title']
        post.slug = request.form['slug']
        post.content = request.form['content']

        db.session.commit()
        flash('Post updated successfully!', 'success')
        return redirect(url_for('admin.posts'))

    return render_template('admin/edit_post.html', post=post)

@admin_routes.route('/post/delete/<int:blog_id>', methods=['POST'])
def delete_post(blog_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin.login'))

    post = BlogPost.query.get_or_404(blog_id)
    db.session.delete(post)
    db.session.commit()
    flash('Post deleted successfully!', 'success')
    return redirect(url_for('admin.posts'))

@admin_routes.route('/change-password', methods=['GET', 'POST'])
def change_password():
    if 'admin_id' not in session:
        return redirect(url_for('admin.login'))

    admin = AdminUser.query.get(session.get('admin_id'))

    if request.method == 'POST':
        current_password = request.form['current_password']
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']

        if not check_password_hash(admin.password_hash, current_password):
            flash('Current password is incorrect.', 'danger')
        elif new_password != confirm_password:
            flash('New passwords do not match.', 'danger')
        else:
            admin.password_hash = generate_password_hash(new_password)
            db.session.commit()
            flash('Password updated successfully!', 'success')
            return redirect(url_for('admin.dashboard'))

    return render_template('admin/change_password.html')

@admin_routes.route('/photos', methods=['GET', 'POST'])
def upload_photos():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin.login'))

    if request.method == 'POST':
        if 'photo' not in request.files:
            flash('No file part', 'danger')
            return redirect(request.url)
        file = request.files['photo']
        if file.filename == '':
            flash('No selected file', 'danger')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)

            os.makedirs(UPLOAD_FOLDER, exist_ok=True)

            file_path = os.path.join(UPLOAD_FOLDER, filename)
            file.save(file_path)

            photo = Photo(filename=filename)
            db.session.add(photo)
            db.session.commit()

            flash('Photo uploaded successfully!', 'success')
            return redirect(url_for('admin.upload_photos'))
        else:
            flash('File type not allowed.', 'danger')

    photos = Photo.query.order_by(Photo.id.desc()).all()
    return render_template('admin/photos.html', photos=photos)

@admin_routes.route('/photo/delete/<int:photo_id>', methods=['POST'])
def delete_photo(photo_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin.login'))

    photo = Photo.query.get_or_404(photo_id)

    file_path = os.path.join(current_app.root_path, 'static/uploads', photo.filename)
    if os.path.exists(file_path):
        os.remove(file_path)

    db.session.delete(photo)
    db.session.commit()
    flash('Photo deleted successfully!', 'success')
    return redirect(url_for('admin.upload_photos'))

@admin_routes.route('/messages')
def view_messages():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin.login'))

    messages = ContactMessage.query.order_by(ContactMessage.created_at.desc()).all()
    return render_template('admin/messages.html', messages=messages)

@admin_routes.route('/message/read/<int:message_id>')
def mark_as_read(message_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin.login'))

    msg = ContactMessage.query.get_or_404(message_id)
    msg.read = not msg.read  # Toggle read status
    db.session.commit()
    return redirect(url_for('admin.view_messages'))



@admin_routes.route('/comment/delete/<int:comment_id>', methods=['POST'])
def delete_comment(comment_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin.login'))

    comment = Comment.query.get_or_404(comment_id)
    db.session.delete(comment)
    db.session.commit()
    flash('Comment deleted successfully!', 'success')

    # ✅ Redirect back to the page the delete was triggered from
    return redirect(url_for('admin.posts', open_post=comment.blog_id))


@admin_routes.route('/comment/approve/<int:comment_id>', methods=['POST'])
def approve_comment(comment_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin.login'))

    comment = Comment.query.get_or_404(comment_id)
    comment.approved = True
    db.session.commit()
    flash('Comment approved successfully!', 'success')
    # ✅ Redirect back to the page the delete was triggered from
    return redirect(url_for('admin.posts', open_post=comment.blog_id))

# ----------------------------
# Like a blog post (admin only)
@admin_routes.route('/like/<int:blog_id>', methods=['POST'])
def like_post(blog_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin.login'))

    post = BlogPost.query.get_or_404(blog_id)
    post.likes = (post.likes or 0) + 1
    db.session.commit()
    # Redirect back to where the like was clicked or admin dashboard
    return redirect(request.referrer or url_for('admin.dashboard'))

# Add a comment to a post (admin only)
@admin_routes.route('/post/<int:blog_id>/comment', methods=['POST'])
def add_comment(blog_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin.login'))

    post = BlogPost.query.get_or_404(blog_id)
    content = request.form.get('content', '').strip()
    if not content:
        flash('Comment cannot be empty.', 'danger')
        return redirect(url_for('admin.view_post', blog_id=post.id))

    comment = Comment(blog_id=post.id, content=content)
    db.session.add(comment)
    db.session.commit()
    flash('Comment added successfully!', 'success')
    return redirect(url_for('admin.view_post', blog_id=post.id))

# Add this route to your existing routes.py file
# Place it after your existing routes

@admin_routes.route('/profile-settings', methods=['GET', 'POST'])
def profile_settings():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin.login'))

    settings = SiteSettings.get_settings()
    
    if request.method == 'POST':
        # Handle profile image upload
        if 'profile_image' in request.files:
            file = request.files['profile_image']
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                
                # Create images folder if it doesn't exist
                images_folder = os.path.join(current_app.root_path, 'static', 'images')
                os.makedirs(images_folder, exist_ok=True)
                
                # Save new profile image
                file_path = os.path.join(images_folder, filename)
                file.save(file_path)
                
                # Delete old profile image if it's not the default
                if settings.profile_image != 'kunal.jpg':
                    old_file_path = os.path.join(images_folder, settings.profile_image)
                    if os.path.exists(old_file_path):
                        os.remove(old_file_path)
                
                # Update settings
                settings.profile_image = filename
                db.session.commit()
                
                flash('Profile image updated successfully!', 'success')
                return redirect(url_for('admin.profile_settings'))
            else:
                flash('Invalid file type. Please upload PNG, JPG, JPEG, or GIF.', 'danger')
        
        # Handle site title update
        site_title = request.form.get('site_title', '').strip()
        if site_title:
            settings.site_title = site_title
            db.session.commit()
            flash('Site title updated successfully!', 'success')
            return redirect(url_for('admin.profile_settings'))

    return render_template('admin/profile_settings.html', settings=settings)

# Also add this import at the top of routes.py
# from .models import AdminUser, BlogPost, Photo, ContactMessage, Comment, SiteSettings