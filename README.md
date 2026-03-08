# InkWell — Blog & Article Publishing Platform

A beginner-friendly Flask web application built as a college assignment.

## Features

- User registration and login with secure password hashing
- Write, edit, delete, and publish blog articles
- Manage personal Skills and Technologies in your dashboard
- Responsive Bootstrap 5 UI with a blue colour theme
- 10+ pages: Home, Blog, Post Detail, About, Contact, Privacy, Cookies, Register, Login, Dashboard

## Tech Stack

| Layer    | Technology           |
|----------|----------------------|
| Backend  | Python / Flask       |
| Database | SQLite + SQLAlchemy  |
| Frontend | Bootstrap 5 + Jinja2 |
| Security | Werkzeug (password hashing) |

## Project Structure

```
blogplatform/
├── app.py              ← Main application: routes, models, config
├── requirements.txt    ← Python dependencies
├── instance/
│   └── blog.db         ← SQLite database (auto-created)
└── templates/
    ├── base.html        ← Shared layout (navbar + footer)
    ├── home.html        ← Landing page
    ├── blog.html        ← Article archive
    ├── post_detail.html ← Individual article
    ├── register.html    ← Sign-up form
    ├── login.html       ← Login form
    ├── dashboard.html   ← User dashboard
    ├── post_form.html   ← Create / edit article
    ├── skill_form.html  ← Add / edit skill
    ├── tech_form.html   ← Add / edit technology
    ├── edit_profile.html
    ├── about.html
    ├── contact.html
    ├── privacy.html
    └── cookies.html
```

## Database Models

| Table          | Description                                |
|----------------|--------------------------------------------|
| `users`        | Registered accounts (username, email, bio) |
| `posts`        | Blog articles (title, content, category)   |
| `skills`       | User skills with proficiency level         |
| `technologies` | Tech stack entries with category           |

## Quick Start

```bash
# 1. Clone the project
git clone <your-repo-url>
cd blogplatform

# 2. Create a virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the app
python app.py
```

Then open your browser at **http://127.0.0.1:5000**

## Notes for Beginners

- `app.py` has detailed comments explaining every section
- The database is created automatically on first run
- Change `SECRET_KEY` in `app.py` before deploying publicly
- Set `debug=False` before deploying to production
