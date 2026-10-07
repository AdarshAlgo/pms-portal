# 🎓 Project Progress Monitoring & Evaluation System

> A comprehensive web application for universities and institutions to track, evaluate, and manage capstone project progress with rubric-based scoring and real-time analytics.

**Aligned with UN SDG 9** — Industry, Innovation, and Infrastructure

---

## 🚀 Features

### Multi-Role Dashboard System
- **Admin/Coordinator**: Manage terms, departments, milestones, rubrics, and view institutional analytics
- **Faculty/Guide**: Review submissions, evaluate with rubrics, log meetings, track team progress
- **Student/Member**: Register projects, submit deliverables, view feedback and progress charts

### Core Modules
- 🔐 **Authentication & RBAC** — Secure bcrypt-hashed passwords with role-based access control
- 📋 **Milestone Lifecycle** — Status flow: Pending → Submitted → Under Review → Approved/Revision/Rejected
- 📊 **Rubric Evaluation Matrix** — Weighted criterion-based scoring with automatic grade computation
- 📈 **Analytics Dashboard** — Chart.js powered progress visualization and burndown charts
- 📝 **Audit & Feedback Logs** — Complete timeline of all review interactions

---

## 🛠️ Technology Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.11+ / Flask 3.x |
| Database | MySQL 8.0 (InnoDB, utf8mb4) |
| ORM | SQLAlchemy + PyMySQL |
| Authentication | Flask-Login + Flask-Bcrypt |
| Frontend | HTML5 + Jinja2 Templates |
| CSS | Tailwind CSS (CDN) |
| Charts | Chart.js |
| Icons | Font Awesome |

---

## 📁 Project Structure

```
├── database/
│   ├── schema.sql          # MySQL DDL (16 normalized tables)
│   └── seed_data.sql       # Sample data for development
├── app/
│   ├── __init__.py          # Flask app factory
│   ├── config.py            # Environment-based configuration
│   ├── extensions.py        # SQLAlchemy, LoginManager, Bcrypt
│   ├── models/              # SQLAlchemy ORM models
│   ├── routes/              # Flask Blueprints (auth, admin, faculty, student, api)
│   ├── services/            # Business logic layer
│   ├── utils/               # RBAC decorators, helpers
│   ├── templates/           # Jinja2 HTML templates
│   └── static/              # CSS, JavaScript, images
├── requirements.txt
├── run.py                   # Application entry point
├── .env.example             # Environment variable template
└── .gitignore
```

---

## ⚡ Quick Start

### Prerequisites
- Python 3.11 or higher
- MySQL 8.0 or higher
- pip (Python package manager)

### 1. Clone and Setup Virtual Environment
```bash
cd "Project Monitoring Software System"
python -m venv venv
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate   # Windows
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Setup MySQL Database
```bash
mysql -u root -p < database/schema.sql
mysql -u root -p project_monitoring_db < database/seed_data.sql
```

### 4. Configure Environment
```bash
cp .env.example .env
# Edit .env with your MySQL credentials
```

### 5. Run the Application
```bash
python run.py
```

The app will be available at `http://localhost:5000`

### Default Login Credentials
| Role | Email | Password |
|------|-------|----------|
| Admin | admin@university.edu | password123 |
| Faculty | dr.smith@university.edu | password123 |
| Student | student1@university.edu | password123 |

---

## 📊 Rubric Scoring Algorithm

The system uses weighted criterion-based evaluation:

```
For each criterion i:
  Normalized Score = marks_obtained / max_marks
  Weighted Score   = normalized_score × weightage%

Total Weighted Score = Σ(weighted_scores)   [out of 100]
Raw Percentage       = (Σ obtained / Σ max) × 100
```

| Grade | Percentage |
|-------|-----------|
| A+ | 90–100% |
| A | 80–89% |
| B+ | 70–79% |
| B | 60–69% |
| C | 50–59% |
| F | Below 50% |

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/progress/<project_id>` | Milestone completion data (Chart.js) |
| `GET` | `/api/scores/<project_id>` | Evaluation scores per milestone |
| `GET` | `/api/department/<dept_id>/stats` | Department analytics |
| `GET` | `/api/notifications` | Unread notifications |
| `POST` | `/api/notifications/<id>/read` | Mark notification as read |

---

## 🔒 Security

- **Passwords**: bcrypt hashing (12 rounds)
- **CSRF**: Flask-WTF token protection on all forms
- **SQL Injection**: SQLAlchemy ORM parameterized queries
- **XSS**: Jinja2 auto-escaping enabled
- **RBAC**: Role-based decorators on every protected route
- **Sessions**: HTTP-only cookies with configurable timeout

---

## 📄 License

This project is developed for academic purposes as a capstone project deliverable.

---

*Built with ❤️ for academic excellence*
