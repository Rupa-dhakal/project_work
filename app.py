# ============================================================
# BLOG / ARTICLE PUBLISHING PLATFORM
# A beginner-friendly Flask web application
# ============================================================

# Import the tools (libraries) we need
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os

# ─── CREATE THE FLASK APP ───────────────────────────────────
app = Flask(__name__)

# Secret key is used to keep sessions (logins) secure
app.config['SECRET_KEY'] = 'my-super-secret-key-change-this-in-production'

# Tell Flask where to store the database file
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blog.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Create the database object
db = SQLAlchemy(app)


# ============================================================
# DATABASE MODELS (Tables)
# Each class below becomes a table in our database
# ============================================================

# TABLE 1: Users — stores everyone who registers on the site
class User(db.Model):
    __tablename__ = 'users'

    id           = db.Column(db.Integer, primary_key=True)           # Unique ID
    username     = db.Column(db.String(80),  unique=True, nullable=False)
    email        = db.Column(db.String(120), unique=True, nullable=False)
    password     = db.Column(db.String(256), nullable=False)          # Hashed password
    full_name    = db.Column(db.String(120), default='')
    bio          = db.Column(db.Text,        default='')
    created_at   = db.Column(db.DateTime,    default=datetime.utcnow)

    # Relationships: one user can have many posts, skills, technologies
    posts        = db.relationship('Post',       backref='author',   lazy=True, cascade='all, delete-orphan')
    skills       = db.relationship('Skill',      backref='user',     lazy=True, cascade='all, delete-orphan')
    technologies = db.relationship('Technology', backref='user',     lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<User {self.username}>'


# TABLE 2: Posts — each blog article lives here
class Post(db.Model):
    __tablename__ = 'posts'

    id           = db.Column(db.Integer, primary_key=True)
    title        = db.Column(db.String(200), nullable=False)
    slug         = db.Column(db.String(220), unique=True, nullable=False)  # URL-friendly title
    content      = db.Column(db.Text,        nullable=False)
    excerpt      = db.Column(db.String(300), default='')               # Short preview
    category     = db.Column(db.String(60),  default='General')
    tags         = db.Column(db.String(200), default='')               # Comma-separated tags
    is_published = db.Column(db.Boolean,     default=True)
    created_at   = db.Column(db.DateTime,    default=datetime.utcnow)
    updated_at   = db.Column(db.DateTime,    default=datetime.utcnow, onupdate=datetime.utcnow)
    user_id      = db.Column(db.Integer,     db.ForeignKey('users.id'), nullable=False)

    def __repr__(self):
        return f'<Post {self.title}>'


# TABLE 3: Skills — things a user knows (Python, Design, etc.)
class Skill(db.Model):
    __tablename__ = 'skills'

    id          = db.Column(db.Integer, primary_key=True)
    name        = db.Column(db.String(100), nullable=False)
    level       = db.Column(db.String(20),  default='Beginner')   # Beginner / Intermediate / Advanced
    description = db.Column(db.Text,        default='')
    user_id     = db.Column(db.Integer,     db.ForeignKey('users.id'), nullable=False)

    def __repr__(self):
        return f'<Skill {self.name}>'


# TABLE 4: Technologies — tools/frameworks a user uses
class Technology(db.Model):
    __tablename__ = 'technologies'

    id          = db.Column(db.Integer, primary_key=True)
    name        = db.Column(db.String(100), nullable=False)
    category    = db.Column(db.String(60),  default='Other')   # Frontend, Backend, Database …
    description = db.Column(db.Text,        default='')
    user_id     = db.Column(db.Integer,     db.ForeignKey('users.id'), nullable=False)

    def __repr__(self):
        return f'<Technology {self.name}>'


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def get_current_user():
    """Return the logged-in User object, or None if not logged in."""
    if 'user_id' in session:
        return User.query.get(session['user_id'])
    return None


def login_required_custom(f):
    """Decorator: redirect to login page if the user is not logged in."""
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access that page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated


def make_slug(title):
    """Turn a title like 'Hello World!' into a URL-safe 'hello-world'."""
    import re
    slug = title.lower()
    slug = re.sub(r'[^\w\s-]', '', slug)
    slug = re.sub(r'[\s_-]+', '-', slug)
    slug = slug.strip('-')
    return slug


# ============================================================
# PUBLIC ROUTES
# ============================================================

@app.route('/')
def home():
    """Home page — shows recent published posts."""
    recent_posts = Post.query.filter_by(is_published=True)\
                             .order_by(Post.created_at.desc())\
                             .limit(6).all()
    categories = db.session.query(Post.category, db.func.count(Post.id))\
                            .filter_by(is_published=True)\
                            .group_by(Post.category).all()
    current_user = get_current_user()
    return render_template('home.html',
                           posts=recent_posts,
                           categories=categories,
                           current_user=current_user)


@app.route('/blog')
def blog():
    """Blog archive — all published posts with optional category filter."""
    category   = request.args.get('category', '')
    page       = request.args.get('page', 1, type=int)

    query = Post.query.filter_by(is_published=True)
    if category:
        query = query.filter_by(category=category)

    posts      = query.order_by(Post.created_at.desc()).paginate(page=page, per_page=6)
    categories = db.session.query(Post.category, db.func.count(Post.id))\
                            .filter_by(is_published=True)\
                            .group_by(Post.category).all()
    current_user = get_current_user()
    return render_template('blog.html',
                           posts=posts,
                           categories=categories,
                           selected_category=category,
                           current_user=current_user)


@app.route('/post/<slug>')
def post_detail(slug):
    """Individual post page."""
    post = Post.query.filter_by(slug=slug, is_published=True).first_or_404()
    # Related posts in same category
    related = Post.query.filter(
        Post.category == post.category,
        Post.id != post.id,
        Post.is_published == True
    ).limit(3).all()
    current_user = get_current_user()
    return render_template('post_detail.html',
                           post=post,
                           related=related,
                           current_user=current_user)


@app.route('/about')
def about():
    current_user = get_current_user()
    return render_template('about.html', current_user=current_user)


@app.route('/contact', methods=['GET', 'POST'])
def contact():
    current_user = get_current_user()
    if request.method == 'POST':
        # In a real app you'd send an email here
        name    = request.form.get('name', '').strip()
        email   = request.form.get('email', '').strip()
        message = request.form.get('message', '').strip()
        if not name or not email or not message:
            flash('Please fill in all fields.', 'danger')
        else:
            flash(f'Thanks {name}! Your message has been received.', 'success')
            return redirect(url_for('contact'))
    return render_template('contact.html', current_user=current_user)


@app.route('/privacy')
def privacy():
    current_user = get_current_user()
    return render_template('privacy.html', current_user=current_user)


@app.route('/cookies')
def cookies():
    current_user = get_current_user()
    return render_template('cookies.html', current_user=current_user)


# ============================================================
# AUTH ROUTES  (Register / Login / Logout)
# ============================================================

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Registration page."""
    current_user = get_current_user()
    if current_user:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username  = request.form.get('username', '').strip()
        email     = request.form.get('email', '').strip()
        password  = request.form.get('password', '')
        password2 = request.form.get('password2', '')

        # --- Server-side validation ---
        error = None
        if not username or not email or not password:
            error = 'All fields are required.'
        elif len(username) < 3:
            error = 'Username must be at least 3 characters.'
        elif len(password) < 6:
            error = 'Password must be at least 6 characters.'
        elif password != password2:
            error = 'Passwords do not match.'
        elif User.query.filter_by(username=username).first():
            error = 'That username is already taken.'
        elif User.query.filter_by(email=email).first():
            error = 'That email is already registered.'

        if error:
            flash(error, 'danger')
        else:
            # Hash the password before saving — NEVER store plain-text passwords
            hashed_pw = generate_password_hash(password)
            new_user  = User(username=username, email=email, password=hashed_pw)
            db.session.add(new_user)
            db.session.commit()
            flash('Account created! You can now log in.', 'success')
            return redirect(url_for('login'))

    return render_template('register.html', current_user=None)


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page."""
    current_user = get_current_user()
    if current_user:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            # Save user ID in the session so we know they're logged in
            session['user_id'] = user.id
            flash(f'Welcome back, {user.username}!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password.', 'danger')

    return render_template('login.html', current_user=None)


@app.route('/logout')
def logout():
    """Log the user out by clearing the session."""
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('home'))


# ============================================================
# DASHBOARD (Protected — must be logged in)
# ============================================================

@app.route('/dashboard')
@login_required_custom
def dashboard():
    user  = get_current_user()
    posts = Post.query.filter_by(user_id=user.id).order_by(Post.created_at.desc()).all()
    skills = Skill.query.filter_by(user_id=user.id).all()
    techs  = Technology.query.filter_by(user_id=user.id).all()
    return render_template('dashboard.html',
                           current_user=user,
                           posts=posts,
                           skills=skills,
                           technologies=techs)


@app.route('/profile/edit', methods=['GET', 'POST'])
@login_required_custom
def edit_profile():
    user = get_current_user()
    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        bio       = request.form.get('bio', '').strip()
        email     = request.form.get('email', '').strip()

        # Check email not taken by someone else
        existing = User.query.filter_by(email=email).first()
        if existing and existing.id != user.id:
            flash('That email is already in use.', 'danger')
        else:
            user.full_name = full_name
            user.bio       = bio
            user.email     = email
            db.session.commit()
            flash('Profile updated!', 'success')
            return redirect(url_for('dashboard'))

    return render_template('edit_profile.html', current_user=user)


# ============================================================
# POSTS CRUD
# ============================================================

@app.route('/post/new', methods=['GET', 'POST'])
@login_required_custom
def new_post():
    user = get_current_user()
    if request.method == 'POST':
        title   = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()
        excerpt = request.form.get('excerpt', '').strip()
        category= request.form.get('category', 'General').strip()
        tags    = request.form.get('tags', '').strip()
        publish = request.form.get('is_published') == 'on'

        if not title or not content:
            flash('Title and content are required.', 'danger')
        else:
            # Create a unique slug
            base_slug = make_slug(title)
            slug = base_slug
            counter = 1
            while Post.query.filter_by(slug=slug).first():
                slug = f'{base_slug}-{counter}'
                counter += 1

            post = Post(
                title=title, slug=slug, content=content,
                excerpt=excerpt, category=category, tags=tags,
                is_published=publish, user_id=user.id
            )
            db.session.add(post)
            db.session.commit()
            flash('Post published!', 'success')
            return redirect(url_for('dashboard'))

    return render_template('post_form.html', current_user=user, post=None)


@app.route('/post/<int:post_id>/edit', methods=['GET', 'POST'])
@login_required_custom
def edit_post(post_id):
    user = get_current_user()
    post = Post.query.get_or_404(post_id)

    # Only the author can edit their post
    if post.user_id != user.id:
        flash('You do not have permission to edit that post.', 'danger')
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        post.title    = request.form.get('title', '').strip()
        post.content  = request.form.get('content', '').strip()
        post.excerpt  = request.form.get('excerpt', '').strip()
        post.category = request.form.get('category', 'General').strip()
        post.tags     = request.form.get('tags', '').strip()
        post.is_published = request.form.get('is_published') == 'on'
        post.updated_at   = datetime.utcnow()

        if not post.title or not post.content:
            flash('Title and content are required.', 'danger')
        else:
            db.session.commit()
            flash('Post updated!', 'success')
            return redirect(url_for('dashboard'))

    return render_template('post_form.html', current_user=user, post=post)


@app.route('/post/<int:post_id>/delete', methods=['POST'])
@login_required_custom
def delete_post(post_id):
    user = get_current_user()
    post = Post.query.get_or_404(post_id)
    if post.user_id != user.id:
        flash('Permission denied.', 'danger')
    else:
        db.session.delete(post)
        db.session.commit()
        flash('Post deleted.', 'info')
    return redirect(url_for('dashboard'))


# ============================================================
# SKILLS CRUD
# ============================================================

@app.route('/skill/new', methods=['GET', 'POST'])
@login_required_custom
def new_skill():
    user = get_current_user()
    if request.method == 'POST':
        name  = request.form.get('name', '').strip()
        level = request.form.get('level', 'Beginner')
        desc  = request.form.get('description', '').strip()
        if not name:
            flash('Skill name is required.', 'danger')
        else:
            skill = Skill(name=name, level=level, description=desc, user_id=user.id)
            db.session.add(skill)
            db.session.commit()
            flash('Skill added!', 'success')
            return redirect(url_for('dashboard'))
    return render_template('skill_form.html', current_user=user, skill=None)


@app.route('/skill/<int:skill_id>/edit', methods=['GET', 'POST'])
@login_required_custom
def edit_skill(skill_id):
    user  = get_current_user()
    skill = Skill.query.get_or_404(skill_id)
    if skill.user_id != user.id:
        flash('Permission denied.', 'danger')
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        skill.name        = request.form.get('name', '').strip()
        skill.level       = request.form.get('level', 'Beginner')
        skill.description = request.form.get('description', '').strip()
        if not skill.name:
            flash('Skill name is required.', 'danger')
        else:
            db.session.commit()
            flash('Skill updated!', 'success')
            return redirect(url_for('dashboard'))
    return render_template('skill_form.html', current_user=user, skill=skill)


@app.route('/skill/<int:skill_id>/delete', methods=['POST'])
@login_required_custom
def delete_skill(skill_id):
    user  = get_current_user()
    skill = Skill.query.get_or_404(skill_id)
    if skill.user_id != user.id:
        flash('Permission denied.', 'danger')
    else:
        db.session.delete(skill)
        db.session.commit()
        flash('Skill removed.', 'info')
    return redirect(url_for('dashboard'))


# ============================================================
# TECHNOLOGIES CRUD
# ============================================================

@app.route('/technology/new', methods=['GET', 'POST'])
@login_required_custom
def new_technology():
    user = get_current_user()
    if request.method == 'POST':
        name     = request.form.get('name', '').strip()
        category = request.form.get('category', 'Other')
        desc     = request.form.get('description', '').strip()
        if not name:
            flash('Technology name is required.', 'danger')
        else:
            tech = Technology(name=name, category=category, description=desc, user_id=user.id)
            db.session.add(tech)
            db.session.commit()
            flash('Technology added!', 'success')
            return redirect(url_for('dashboard'))
    return render_template('tech_form.html', current_user=user, tech=None)


@app.route('/technology/<int:tech_id>/edit', methods=['GET', 'POST'])
@login_required_custom
def edit_technology(tech_id):
    user = get_current_user()
    tech = Technology.query.get_or_404(tech_id)
    if tech.user_id != user.id:
        flash('Permission denied.', 'danger')
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        tech.name        = request.form.get('name', '').strip()
        tech.category    = request.form.get('category', 'Other')
        tech.description = request.form.get('description', '').strip()
        if not tech.name:
            flash('Technology name is required.', 'danger')
        else:
            db.session.commit()
            flash('Technology updated!', 'success')
            return redirect(url_for('dashboard'))
    return render_template('tech_form.html', current_user=user, tech=tech)


@app.route('/technology/<int:tech_id>/delete', methods=['POST'])
@login_required_custom
def delete_technology(tech_id):
    user = get_current_user()
    tech = Technology.query.get_or_404(tech_id)
    if tech.user_id != user.id:
        flash('Permission denied.', 'danger')
    else:
        db.session.delete(tech)
        db.session.commit()
        flash('Technology removed.', 'info')
    return redirect(url_for('dashboard'))


# ============================================================
# RUN THE APP
# ============================================================

if __name__ == '__main__':
    # Create all database tables if they don't exist yet
    with app.app_context():
        db.create_all()
        print("✅ Database tables created.")
    # debug=True shows helpful error pages during development
    # Change to debug=False before deploying to the public!
    app.run(debug=True)
