import sqlite3
import sys


# Creates and populates a test SQLite database.
# Drops and recreates all tables, then inserts sample data.
def create_test_db(db_name="test.db"):
    conn = sqlite3.connect(db_name)
    cur = conn.cursor()

    cur.executescript("""
        DROP TABLE IF EXISTS payments;
        DROP TABLE IF EXISTS certificates;
        DROP TABLE IF EXISTS grades;
        DROP TABLE IF EXISTS completion;
        DROP TABLE IF EXISTS lessons;
        DROP TABLE IF EXISTS modules;
        DROP TABLE IF EXISTS enrollments;
        DROP TABLE IF EXISTS courses;
        DROP TABLE IF EXISTS users;

        CREATE TABLE users (
            uid         INTEGER,
            name        TEXT,
            email       TEXT,
            role        TEXT,
            pwd         TEXT,
            PRIMARY KEY (uid)
        );

        CREATE TABLE courses (
            cid             INTEGER,
            title           TEXT,
            description     TEXT,
            category        TEXT,
            price           REAL,
            pass_grade      REAL,
            max_students    INTEGER,
            PRIMARY KEY (cid)
        );

        CREATE TABLE enrollments (
            cid         INTEGER,
            uid         INTEGER,
            start_ts    TEXT,
            end_ts      TEXT,
            role        TEXT,
            FOREIGN KEY (cid) REFERENCES courses(cid),
            FOREIGN KEY (uid) REFERENCES users(uid)
        );

        CREATE TABLE modules (
            cid         INTEGER,
            mid         INTEGER,
            name        TEXT,
            summary     TEXT,
            weight      REAL,
            PRIMARY KEY (cid, mid),
            FOREIGN KEY (cid) REFERENCES courses(cid)
        );

        CREATE TABLE lessons (
            cid         INTEGER,
            mid         INTEGER,
            lid         INTEGER,
            title       TEXT,
            duration    INTEGER,
            content     TEXT,
            PRIMARY KEY (cid, mid, lid),
            FOREIGN KEY (cid, mid) REFERENCES modules(cid, mid)
        );

        CREATE TABLE completion (
            uid         INTEGER,
            cid         INTEGER,
            mid         INTEGER,
            lid         INTEGER,
            ts          TEXT,
            PRIMARY KEY (uid, cid, mid, lid),
            FOREIGN KEY (uid) REFERENCES users(uid),
            FOREIGN KEY (cid, mid, lid) REFERENCES lessons(cid, mid, lid)
        );

        CREATE TABLE grades (
            uid         INTEGER,
            cid         INTEGER,
            mid         INTEGER,
            received_ts TEXT,
            grade       REAL,
            PRIMARY KEY (uid, cid, mid),
            FOREIGN KEY (uid) REFERENCES users(uid),
            FOREIGN KEY (cid, mid) REFERENCES modules(cid, mid)
        );

        CREATE TABLE certificates (
            cid         INTEGER,
            uid         INTEGER,
            received_ts TEXT,
            final_grade REAL,
            PRIMARY KEY (cid, uid),
            FOREIGN KEY (cid) REFERENCES courses(cid),
            FOREIGN KEY (uid) REFERENCES users(uid)
        );

        CREATE TABLE payments (
            uid             INTEGER,
            cid             INTEGER,
            ts              TEXT,
            credit_card_no  TEXT,
            expiry_date     TEXT,
            FOREIGN KEY (uid) REFERENCES users(uid),
            FOREIGN KEY (cid) REFERENCES courses(cid)
        );
    """)

    users = [
        (1,  'Alice Johnson',   'alice@example.com',    'Student',      'pass123'),
        (2,  'Bob Smith',       'bob@example.com',      'Student',      'pass456'),
        (3,  'Charlie Brown',   'charlie@example.com',  'Student',      'pass789'),
        (4,  'Diana Prince',    'diana@example.com',    'Instructor',   'instpass1'),
        (5,  'Eve Adams',       'eve@example.com',      'Instructor',   'instpass2'),
        (6,  'Frank Castle',    'frank@example.com',    'Admin',        'adminpass'),
        (7,  'Grace Lee',       'grace@example.com',    'Student',      'pass321'),
        (8,  'Hank Pym',        'hank@example.com',     'Student',      'pass654'),
        (9,  'Ivy Chen',        'ivy@example.com',      'Student',      'pass987'),
        (10, 'Jack Daniels',    'jack@example.com',     'Student',      'pass111'),
    ]
    cur.executemany("INSERT INTO users VALUES (?,?,?,?,?)", users)

    courses = [
        (101, 'Intro to Python',          'Learn Python from scratch with hands-on projects',   'Programming',    49.99,  60.0, 5),
        (102, 'Web Development',           'Full-stack web development with HTML CSS and JS',    'Programming',    79.99,  70.0, 3),
        (103, 'Data Science Fundamentals', 'Introduction to data analysis and visualization',   'Data',           99.99,  65.0, 10),
        (104, 'Machine Learning',          'Advanced ML algorithms and neural networks',         'Data',          149.99,  75.0, 2),
        (105, 'Digital Marketing',         'SEO social media and content marketing strategies',  'Marketing',      29.99,  50.0, 20),
        (106, 'Cybersecurity Basics',      'Network security and ethical hacking fundamentals',  'Security',       89.99,  70.0, 8),
        (107, 'Cloud Computing',           'AWS Azure and cloud architecture patterns',          'Infrastructure', 119.99, 65.0, 5),
        (108, 'Mobile App Development',    'Build iOS and Android apps with React Native',       'Programming',    69.99,  60.0, 15),
    ]
    cur.executemany("INSERT INTO courses VALUES (?,?,?,?,?,?,?)", courses)

    enrollments = [
        # Instructor enrollments
        (101, 4, '2025-01-01 09:00:00', '2027-01-01 09:00:00', 'Instructor'),
        (102, 4, '2025-01-01 09:00:00', '2027-01-01 09:00:00', 'Instructor'),
        (108, 4, '2025-01-01 09:00:00', '2027-01-01 09:00:00', 'Instructor'),
        (103, 5, '2025-01-01 09:00:00', '2027-01-01 09:00:00', 'Instructor'),
        (104, 5, '2025-01-01 09:00:00', '2027-01-01 09:00:00', 'Instructor'),
        (105, 5, '2025-01-01 09:00:00', '2027-01-01 09:00:00', 'Instructor'),
        (106, 5, '2025-01-01 09:00:00', '2027-01-01 09:00:00', 'Instructor'),
        (107, 5, '2025-01-01 09:00:00', '2027-01-01 09:00:00', 'Instructor'),

        # Active student enrollments
        (101, 1, '2025-09-01 10:00:00', '2026-09-01 10:00:00', 'Student'),
        (103, 1, '2025-10-15 14:00:00', '2026-10-15 14:00:00', 'Student'),
        (106, 1, '2026-01-10 08:00:00', '2027-01-10 08:00:00', 'Student'),
        (101, 2, '2025-09-05 11:00:00', '2026-09-05 11:00:00', 'Student'),
        (102, 2, '2025-11-01 09:00:00', '2026-11-01 09:00:00', 'Student'),
        (104, 2, '2026-01-15 13:00:00', '2027-01-15 13:00:00', 'Student'),
        (103, 3, '2025-10-20 10:00:00', '2026-10-20 10:00:00', 'Student'),
        (104, 3, '2026-02-01 15:00:00', '2027-02-01 15:00:00', 'Student'),
        (101, 7, '2026-01-05 09:00:00', '2027-01-05 09:00:00', 'Student'),
        (105, 7, '2026-02-10 10:00:00', '2027-02-10 10:00:00', 'Student'),
        (105, 9, '2026-01-20 11:00:00', '2027-01-20 11:00:00', 'Student'),
        (106, 9, '2026-02-15 14:00:00', '2027-02-15 14:00:00', 'Student'),
        (107, 10, '2026-01-08 08:00:00', '2027-01-08 08:00:00', 'Student'),

        # Expired enrollments
        (102, 1, '2024-06-01 10:00:00', '2025-06-01 10:00:00', 'Student'),
        (105, 2, '2024-09-01 09:00:00', '2025-09-01 09:00:00', 'Student'),
    ]
    cur.executemany("INSERT INTO enrollments VALUES (?,?,?,?,?)", enrollments)

    modules = [
        (101, 1, 'Python Basics',       'Variables types and control flow',         0.30),
        (101, 2, 'Functions and OOP',   'Functions classes and object orientation', 0.40),
        (101, 3, 'File I/O',            'Reading writing and processing files',     0.30),
        (102, 1, 'HTML and CSS',        'Building and styling web pages',           0.40),
        (102, 2, 'JavaScript',          'Client-side scripting and DOM',            0.60),
        (103, 1, 'Statistics',          'Descriptive and inferential statistics',   0.30),
        (103, 2, 'Pandas and NumPy',    'Data manipulation with Python libraries',  0.40),
        (103, 3, 'Visualization',       'Charts and dashboards with matplotlib',    0.30),
        (104, 1, 'Supervised Learning', 'Regression and classification algorithms', 0.50),
        (104, 2, 'Neural Networks',     'Deep learning with TensorFlow',            0.50),
        (105, 1, 'SEO Fundamentals',    'Search engine optimization techniques',    0.50),
        (105, 2, 'Social Media',        'Platform strategies and analytics',        0.50),
        (106, 1, 'Network Security',    'Firewalls encryption and protocols',       0.50),
        (106, 2, 'Ethical Hacking',     'Penetration testing methodologies',        0.50),
        (107, 1, 'Cloud Fundamentals',  'IaaS PaaS SaaS and deployment models',    0.40),
        (107, 2, 'AWS Services',        'EC2 S3 Lambda and cloud architecture',     0.60),
        (108, 1, 'React Native Basics', 'Components state and navigation',          0.50),
        (108, 2, 'Native APIs',         'Camera GPS and push notifications',        0.50),
    ]
    cur.executemany("INSERT INTO modules VALUES (?,?,?,?,?)", modules)

    lessons = [
        (101, 1, 1, 'Installing Python',       15, 'Download Python from python.org and set up your environment.'),
        (101, 1, 2, 'Variables and Types',      30, 'Learn about int float str bool and type conversion.'),
        (101, 1, 3, 'Control Flow',             25, 'If-else statements for-loops and while-loops explained.'),
        (101, 2, 1, 'Defining Functions',       20, 'How to create reusable functions with parameters.'),
        (101, 2, 2, 'Classes and Objects',      35, 'Object-oriented programming with Python classes.'),
        (101, 2, 3, 'Inheritance',              30, 'Extending classes with inheritance and polymorphism.'),
        (101, 3, 1, 'Reading Files',            20, 'Open read and parse text and CSV files.'),
        (101, 3, 2, 'Writing Files',            20, 'Write output to text JSON and CSV files.'),
        (102, 1, 1, 'HTML Structure',           25, 'Tags attributes and semantic HTML5 elements.'),
        (102, 1, 2, 'CSS Styling',              30, 'Selectors properties flexbox and grid layout.'),
        (102, 2, 1, 'JS Basics',                25, 'Variables functions and event handling.'),
        (102, 2, 2, 'DOM Manipulation',         30, 'Selecting and modifying HTML elements with JavaScript.'),
        (103, 1, 1, 'Descriptive Stats',        20, 'Mean median mode and standard deviation.'),
        (103, 1, 2, 'Probability',              25, 'Basic probability distributions and Bayes theorem.'),
        (103, 2, 1, 'Pandas Intro',             30, 'DataFrames series and data loading.'),
        (103, 2, 2, 'Data Cleaning',            25, 'Handling missing values and data transformation.'),
        (103, 3, 1, 'Matplotlib Basics',        20, 'Line plots bar charts and histograms.'),
        (103, 3, 2, 'Advanced Plots',           25, 'Heatmaps subplots and interactive dashboards.'),
        (104, 1, 1, 'Linear Regression',        30, 'Fitting lines to data and evaluating models.'),
        (104, 1, 2, 'Classification',           35, 'Decision trees random forests and SVM.'),
        (104, 2, 1, 'Neural Net Basics',        40, 'Perceptrons activation functions and backpropagation.'),
        (104, 2, 2, 'Building with TensorFlow', 45, 'Creating training and evaluating deep learning models.'),
        (105, 1, 1, 'Keyword Research',         20, 'Finding and targeting the right search terms.'),
        (105, 1, 2, 'On-Page SEO',              20, 'Meta tags content structure and internal linking.'),
        (105, 2, 1, 'Platform Strategy',        25, 'Choosing platforms and content calendars.'),
        (105, 2, 2, 'Analytics',                20, 'Measuring engagement reach and conversions.'),
        (106, 1, 1, 'Firewall Config',          25, 'Setting up and managing network firewalls.'),
        (106, 1, 2, 'Encryption',               30, 'Symmetric asymmetric and hashing algorithms.'),
        (106, 2, 1, 'Vulnerability Scanning',   30, 'Tools and techniques for finding weaknesses.'),
        (106, 2, 2, 'Pen Testing',              35, 'Conducting authorized penetration tests.'),
        (107, 1, 1, 'Cloud Models',             20, 'Understanding IaaS PaaS and SaaS differences.'),
        (107, 1, 2, 'Deployment',               25, 'Deploying applications to the cloud.'),
        (107, 2, 1, 'EC2 and S3',               30, 'Compute and storage services in AWS.'),
        (107, 2, 2, 'Lambda Functions',         25, 'Serverless computing with AWS Lambda.'),
        (108, 1, 1, 'Components',               25, 'Building UI with React Native components.'),
        (108, 1, 2, 'State Management',         30, 'Managing app state with hooks and context.'),
        (108, 2, 1, 'Camera API',               20, 'Accessing device camera in React Native.'),
        (108, 2, 2, 'Push Notifications',       25, 'Setting up push notification services.'),
    ]
    cur.executemany("INSERT INTO lessons VALUES (?,?,?,?,?,?)", lessons)

    completion = [
        # Alice completed all 8 lessons in course 101
        (1, 101, 1, 1, '2025-09-10 10:00:00'),
        (1, 101, 1, 2, '2025-09-12 11:00:00'),
        (1, 101, 1, 3, '2025-09-15 14:00:00'),
        (1, 101, 2, 1, '2025-09-20 10:00:00'),
        (1, 101, 2, 2, '2025-09-25 15:00:00'),
        (1, 101, 2, 3, '2025-10-01 09:00:00'),
        (1, 101, 3, 1, '2025-10-05 11:00:00'),
        (1, 101, 3, 2, '2025-10-08 13:00:00'),
        # Alice completed 4 of 6 lessons in course 103
        (1, 103, 1, 1, '2025-11-01 10:00:00'),
        (1, 103, 1, 2, '2025-11-05 11:00:00'),
        (1, 103, 2, 1, '2025-11-10 14:00:00'),
        (1, 103, 2, 2, '2025-11-15 09:00:00'),
        # Bob completed 5 of 8 lessons in course 101
        (2, 101, 1, 1, '2025-09-15 10:00:00'),
        (2, 101, 1, 2, '2025-09-18 11:00:00'),
        (2, 101, 1, 3, '2025-09-22 14:00:00'),
        (2, 101, 2, 1, '2025-10-01 10:00:00'),
        (2, 101, 2, 2, '2025-10-05 15:00:00'),
        # Bob completed all 4 lessons in course 102
        (2, 102, 1, 1, '2025-11-10 10:00:00'),
        (2, 102, 1, 2, '2025-11-15 11:00:00'),
        (2, 102, 2, 1, '2025-11-20 14:00:00'),
        (2, 102, 2, 2, '2025-11-25 09:00:00'),
        # Charlie completed all 6 lessons in course 103
        (3, 103, 1, 1, '2025-11-01 10:00:00'),
        (3, 103, 1, 2, '2025-11-03 11:00:00'),
        (3, 103, 2, 1, '2025-11-08 14:00:00'),
        (3, 103, 2, 2, '2025-11-12 09:00:00'),
        (3, 103, 3, 1, '2025-11-18 10:00:00'),
        (3, 103, 3, 2, '2025-11-22 15:00:00'),
        # Grace completed 3 of 8 lessons in course 101
        (7, 101, 1, 1, '2026-01-15 10:00:00'),
        (7, 101, 1, 2, '2026-01-20 11:00:00'),
        (7, 101, 1, 3, '2026-01-25 14:00:00'),
    ]
    cur.executemany("INSERT INTO completion VALUES (?,?,?,?,?)", completion)

    grades = [
        # Alice: all 3 modules graded in course 101 -- final_grade = 84.3
        (1, 101, 1, '2025-10-10 10:00:00', 85.0),
        (1, 101, 2, '2025-10-20 10:00:00', 78.0),
        (1, 101, 3, '2025-10-25 10:00:00', 92.0),
        # Alice: 2 of 3 modules graded in course 103
        (1, 103, 1, '2025-12-01 10:00:00', 70.0),
        (1, 103, 2, '2025-12-10 10:00:00', 75.0),
        # Bob: 2 of 3 modules graded in course 101
        (2, 101, 1, '2025-10-15 10:00:00', 90.0),
        (2, 101, 2, '2025-10-28 10:00:00', 65.0),
        # Bob: all 2 modules graded in course 102 -- final_grade = 75.2
        (2, 102, 1, '2025-12-01 10:00:00', 80.0),
        (2, 102, 2, '2025-12-15 10:00:00', 72.0),
        # Charlie: all 3 modules graded in course 103 -- final_grade = 88.7
        (3, 103, 1, '2025-12-05 10:00:00', 88.0),
        (3, 103, 2, '2025-12-15 10:00:00', 92.0),
        (3, 103, 3, '2025-12-20 10:00:00', 85.0),
    ]
    cur.executemany("INSERT INTO grades VALUES (?,?,?,?,?)", grades)

    certificates = [
        # Alice: completed all lessons in 101, final_grade=84.3 >= pass_grade=60
        (101, 1, '2025-10-30 10:00:00', 84.3),
        # Bob: completed all lessons in 102, final_grade=75.2 >= pass_grade=70
        (102, 2, '2025-12-20 10:00:00', 75.2),
        # Charlie: completed all lessons in 103, final_grade=88.7 >= pass_grade=65
        (103, 3, '2025-12-25 10:00:00', 88.7),
    ]
    cur.executemany("INSERT INTO certificates VALUES (?,?,?,?)", certificates)

    payments = [
        (1, 101, '2025-09-01 10:00:00', '4111111111111234', '06/2027'),
        (1, 103, '2025-10-15 14:00:00', '4111111111111234', '06/2027'),
        (1, 106, '2026-01-10 08:00:00', '4111111111115678', '12/2027'),
        (2, 101, '2025-09-05 11:00:00', '5222333344441111', '03/2028'),
        (2, 102, '2025-11-01 09:00:00', '5222333344441111', '03/2028'),
        (2, 104, '2026-01-15 13:00:00', '5222333344442222', '09/2027'),
        (3, 103, '2025-10-20 10:00:00', '3411223344559999', '05/2027'),
        (3, 104, '2026-02-01 15:00:00', '3411223344559999', '05/2027'),
        (7, 101, '2026-01-05 09:00:00', '6011444455556666', '11/2027'),
        (7, 105, '2026-02-10 10:00:00', '6011444455556666', '11/2027'),
        (9, 105, '2026-01-20 11:00:00', '4999888877773333', '08/2027'),
        (9, 106, '2026-02-15 14:00:00', '4999888877773333', '08/2027'),
        (10, 107, '2026-01-08 08:00:00', '3712345678904444', '04/2028'),
        
        # Expired enrollment payments kept for historical record
        (1, 102, '2024-06-01 10:00:00', '4111111111111234', '06/2027'),
        (2, 105, '2024-09-01 09:00:00', '5222333344441111', '03/2028'),
    ]
    cur.executemany("INSERT INTO payments VALUES (?,?,?,?,?)", payments)

    conn.commit()
    conn.close()
    print(f"Test database '{db_name}' created successfully!")


if __name__ == '__main__':
    name = sys.argv[1] if len(sys.argv) > 1 else 'test.db'
    create_test_db(name)