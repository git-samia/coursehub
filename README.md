# CourseHub

A role-based course management platform built with Python and SQLite. CourseHub provides a complete learning ecosystem where students can discover and enroll in courses, track their progress, and earn certificates — while instructors and admins manage content and monitor platform analytics.

## Features

**Students**
- Search and browse courses with filters (keyword, category, price range)
- Enroll in courses with payment processing and card validation
- Navigate structured content: courses > modules > lessons
- Track lesson completion and view weighted grades
- Earn certificates upon passing a course

**Instructors**
- Manage course settings (pricing, pass grade, capacity)
- Override enrollment to manually add students
- View course statistics: active enrollment, completion rates, average grades
- Automatic certificate re-evaluation when pass grades are updated

**Admins**
- View platform-wide analytics
- Top courses ranked by enrollment (with tie handling)
- Payment activity breakdown per course

## Database Schema

The platform is backed by a relational schema with 9 tables:

```
users ─── enrollments ─── courses ─── modules ─── lessons
              │                          │           │
           payments                    grades    completion
                                         │
                                    certificates
```

## Tech Stack

- **Python 3** — standard library only (`sqlite3`, `getpass`, `datetime`)
- **SQLite** — lightweight relational database, zero configuration
- **CLI interface** — paginated menus with role-based access control

## Getting Started

**1. Clone the repository**

```bash
git clone https://github.com/git-samia/coursehub.git
cd coursehub
```

**2. Set up the database**

```bash
python create_test_db.py
```

This generates `test.db` with sample users, courses, and enrollment data.

**3. Run the application**

```bash
python prj.py test.db
```

**4. Log in with a test account**

| Role       | Email               | Password    |
|------------|---------------------|-------------|
| Student    | alice@example.com   | pass123     |
| Instructor | diana@example.com   | instpass1   |
| Admin      | frank@example.com   | adminpass   |

## Project Structure

```
coursehub/
├── prj.py              # Entry point — authentication and routing
├── student.py          # Student workflows and course interaction
├── instructor.py       # Instructor management and analytics
├── admin.py            # Admin dashboard and platform statistics
├── helpers.py          # Shared utilities (pagination, validation, formatting)
└── create_test_db.py   # Database schema and seed data
```
