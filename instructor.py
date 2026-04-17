from helpers import get_current_ts, get_end_ts, paginate


# Displays the instructor main menu and directs to update course, override enrollment,
# course stats, logout, or exit based on the instructor's input
def instructor_menu(conn, uid):
    while True:
        print("\n========== Instructor Menu ==========")
        print("1. Update course")
        print("2. Override enrollment")
        print("3. Course stats")
        print("4. Logout")
        print("5. Exit")

        choice = input("Enter choice: ").strip()

        if choice == '1':
            update_course(conn, uid)
        elif choice == '2':
            override_enrollment(conn, uid)
        elif choice == '3':
            course_stats(conn, uid)
        elif choice == '4':
            return 'logout'
        elif choice == '5':
            return 'exit'
        else:
            print("Invalid choice.")


# Queries the database for all courses where the given uid has an Instructor enrollment,
# and returns them with current active student enrollment counts
def get_instructor_courses(conn, uid):
    now = get_current_ts()
    cur = conn.cursor()
    cur.execute("""
        SELECT DISTINCT c.cid, c.title, c.category, c.price, c.pass_grade, c.max_students,
               (SELECT COUNT(*) FROM enrollments e2
                WHERE e2.cid = c.cid AND e2.role = 'Student'
                AND e2.start_ts <= ? AND e2.end_ts >= ?) AS current_enrollment
        FROM courses c
        JOIN enrollments e ON c.cid = e.cid
        WHERE e.uid = ? AND e.role = 'Instructor'
    """, (now, now, uid))
    return cur.fetchall()


# Lets the instructor select one of their courses and update its price, pass_grade,
# and/or max_students; validates each field individually before applying the update,
# re-evaluates certificates if pass_grade changed, and loops so the instructor can
# update again or go back to the menu
def update_course(conn, uid):
    courses = get_instructor_courses(conn, uid)
    if not courses:
        print("\nYou have no courses to update.")
        return

    columns = ['cid', 'title', 'category', 'price', 'pass_grade', 'max_students', 'current_enrollment']
    selected = paginate(courses, columns, allow_select=True, id_index=0)
    if not selected:
        return

    cid = selected[0]

    while True:
        now = get_current_ts()
        cur = conn.cursor()
        cur.execute("""
            SELECT c.cid, c.title, c.category, c.price, c.pass_grade, c.max_students,
                   (SELECT COUNT(*) FROM enrollments e2
                    WHERE e2.cid = c.cid AND e2.role = 'Student'
                    AND e2.start_ts <= ? AND e2.end_ts >= ?) AS current_enrollment
            FROM courses c WHERE c.cid = ?
        """, (now, now, cid))
        row = cur.fetchone()
        if not row:
            print("Course not found.")
            return

        print(f"\n========== Course Details ==========")
        print(f"  cid: {row[0]}")
        print(f"  title: {row[1]}")
        print(f"  category: {row[2]}")
        print(f"  price: {row[3]}")
        print(f"  pass_grade: {row[4]}")
        print(f"  max_students: {row[5]}")
        print(f"  current_enrollment: {row[6]}")

        old_price = row[3]
        old_pass_grade = row[4]
        old_max = row[5]

        new_price_str = input("\nNew price (blank to keep): ").strip()
        try:
            price = float(new_price_str) if new_price_str else old_price
        except ValueError:
            print("Invalid price. Must be a number.")
            continue
        if price < 0:
            print("Price cannot be negative.")
            continue

        new_pg_str = input("New pass_grade (blank to keep): ").strip()
        try:
            pass_grade = float(new_pg_str) if new_pg_str else old_pass_grade
        except ValueError:
            print("Invalid pass_grade. Must be a number.")
            continue
        if pass_grade < 0 or pass_grade > 100:
            print("Pass grade must be between 0 and 100.")
            continue

        new_max_str = input("New max_students (blank to keep): ").strip()
        try:
            max_students = int(new_max_str) if new_max_str else old_max
        except ValueError:
            print("Invalid max_students. Must be a whole number.")
            continue
        if max_students <= 0:
            print("Max students must be a positive number.")
            continue

        cur.execute("""
            UPDATE courses SET price = ?, pass_grade = ?, max_students = ?
            WHERE cid = ?
        """, (price, pass_grade, max_students, cid))
        conn.commit()

        added, removed = 0, 0
        if pass_grade != old_pass_grade:
            added, removed = reevaluate_certificates(conn, cid, pass_grade)

        print("\n========== Update Result ==========")
        print(f"  cid: {cid}")
        print(f"  price: {price}")
        print(f"  pass_grade: {pass_grade}")
        print(f"  max_students: {max_students}")
        print(f"  certificates_added: {added}")
        print(f"  certificates_removed: {removed}")

        input("\nPress Enter to continue...")

        go_back = input("Update again? (y/n): ").strip().lower()
        if go_back != 'y':
            return


# After a pass_grade update, checks every actively enrolled student in the course
# to determine if they qualify for a certificate based on completing all lessons
# and achieving a weighted final grade >= the new pass_grade; inserts missing
# certificates for newly qualifying students and deletes certificates for those
# who no longer qualify, returning the counts of added and removed certificates
def reevaluate_certificates(conn, cid, pass_grade):
    cur = conn.cursor()
    now = get_current_ts()

    cur.execute("""
        SELECT e.uid FROM enrollments e
        WHERE e.cid = ? AND e.role = 'Student'
        AND e.start_ts <= ? AND e.end_ts >= ?
    """, (cid, now, now))
    students = cur.fetchall()

    cur.execute("SELECT COUNT(*) FROM lessons WHERE cid = ?", (cid,))
    total_lessons = cur.fetchone()[0]

    added = 0
    removed = 0

    for (student_uid,) in students:
        cur.execute(
            "SELECT COUNT(*) FROM completion WHERE uid = ? AND cid = ?",
            (student_uid, cid)
        )
        completed = cur.fetchone()[0]
        all_done = completed >= total_lessons and total_lessons > 0

        cur.execute("""
            SELECT SUM(g.grade * m.weight) / SUM(m.weight)
            FROM grades g
            JOIN modules m ON g.cid = m.cid AND g.mid = m.mid
            WHERE g.uid = ? AND g.cid = ?
        """, (student_uid, cid))
        result = cur.fetchone()
        final_grade = result[0] if result and result[0] is not None else None

        qualifies = all_done and final_grade is not None and final_grade >= pass_grade

        cur.execute("SELECT 1 FROM certificates WHERE cid = ? AND uid = ?", (cid, student_uid))
        has_cert = cur.fetchone() is not None

        if qualifies and not has_cert:
            cur.execute("""
                INSERT INTO certificates (cid, uid, received_ts, final_grade)
                VALUES (?, ?, ?, ?)
            """, (cid, student_uid, now, final_grade))
            added += 1
        elif not qualifies and has_cert:
            cur.execute("DELETE FROM certificates WHERE cid = ? AND uid = ?", (cid, student_uid))
            removed += 1

    conn.commit()
    return added, removed


# Lets the instructor select one of their courses and manually enroll a student by uid,
# bypassing the max_students cap; validates that the uid belongs to a Student role and
# that the student is not already actively enrolled, then inserts enrollment and payment
# records; loops so the instructor can enroll additional students in the same course
# or go back to the course selection page
def override_enrollment(conn, uid):
    courses = get_instructor_courses(conn, uid)
    if not courses:
        print("\nYou have no courses.")
        return

    columns = ['cid', 'title', 'category', 'price', 'pass_grade', 'max_students', 'current_enrollment']
    selected = paginate(courses, columns, allow_select=True, id_index=0)
    if not selected:
        return

    cid = selected[0]
    course_title = selected[1]

    while True:
        student_uid_input = input("\nEnter student user ID: ").strip()
        try:
            student_uid = int(student_uid_input)
        except ValueError:
            student_uid = student_uid_input

        cur = conn.cursor()
        cur.execute("SELECT uid, name FROM users WHERE uid = ? AND role = 'Student'", (student_uid,))
        student = cur.fetchone()

        if not student:
            print("User not found or is not a Student.")
        else:
            now = get_current_ts()
            cur.execute("""
                SELECT 1 FROM enrollments
                WHERE cid = ? AND uid = ? AND role = 'Student'
                AND start_ts <= ? AND end_ts >= ?
            """, (cid, student_uid, now, now))

            if cur.fetchone():
                print("Student is already actively enrolled in this course.")
            else:
                start_ts = now
                end_ts = get_end_ts()

                cur.execute("""
                    INSERT INTO enrollments (cid, uid, start_ts, end_ts, role)
                    VALUES (?, ?, ?, ?, 'Student')
                """, (cid, student_uid, start_ts, end_ts))

                cur.execute("""
                    INSERT INTO payments (uid, cid, ts, credit_card_no, expiry_date)
                    VALUES (?, ?, ?, '0000000000000000', '12/2026')
                """, (student_uid, cid, start_ts))

                conn.commit()

                print("\n========== Override Enrollment Confirmation ==========")
                print(f"  cid: {cid}")
                print(f"  course_title: {course_title}")
                print(f"  uid: {student_uid}")
                print(f"  student_name: {student[1]}")
                print(f"  start_ts: {start_ts}")

        again = input("\nEnroll another student in this course? (y/n): ").strip().lower()
        if again != 'y':
            return


# Retrieves and displays a summary table for all courses the instructor teaches,
# showing active enrollment count, the percentage of actively enrolled students
# who have completed all lessons in the course, and the average weighted final grade
# across students who have received at least one module grade
def course_stats(conn, uid):
    now = get_current_ts()
    cur = conn.cursor()

    cur.execute("""
        SELECT DISTINCT c.cid, c.title
        FROM courses c
        JOIN enrollments e ON c.cid = e.cid
        WHERE e.uid = ? AND e.role = 'Instructor'
    """, (uid,))
    courses = cur.fetchall()

    if not courses:
        print("\nNo courses found.")
        return

    rows = []
    for course_cid, title in courses:
        cur.execute("""
            SELECT COUNT(*) FROM enrollments
            WHERE cid = ? AND role = 'Student'
            AND start_ts <= ? AND end_ts >= ?
        """, (course_cid, now, now))
        active = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM lessons WHERE cid = ?", (course_cid,))
        total_lessons = cur.fetchone()[0]

        cur.execute("""
            SELECT uid FROM enrollments
            WHERE cid = ? AND role = 'Student'
            AND start_ts <= ? AND end_ts >= ?
        """, (course_cid, now, now))
        active_students = cur.fetchall()

        completed_count = 0
        total_fg = 0.0
        fg_count = 0

        for (s_uid,) in active_students:
            if total_lessons > 0:
                cur.execute(
                    "SELECT COUNT(*) FROM completion WHERE uid = ? AND cid = ?",
                    (s_uid, course_cid)
                )
                if cur.fetchone()[0] >= total_lessons:
                    completed_count += 1

            cur.execute("""
                SELECT SUM(g.grade * m.weight) / SUM(m.weight)
                FROM grades g
                JOIN modules m ON g.cid = m.cid AND g.mid = m.mid
                WHERE g.uid = ? AND g.cid = ?
            """, (s_uid, course_cid))
            fg = cur.fetchone()
            if fg and fg[0] is not None:
                total_fg += fg[0]
                fg_count += 1

        comp_rate = f"{(completed_count / active * 100):.1f}%" if active > 0 else "0.0%"
        avg_fg = f"{(total_fg / fg_count):.2f}" if fg_count > 0 else "N/A"

        rows.append((course_cid, title, active, comp_rate, avg_fg))

    columns = ['cid', 'title', 'active_enrollment', 'completion_rate', 'average_final_grade']
    print("\n========== Course Statistics ==========")
    widths = []
    for i in range(len(columns)):
        w = len(columns[i])
        for row in rows:
            w = max(w, len(str(row[i])))
        widths.append(w)

    header = " | ".join(columns[i].ljust(widths[i]) for i in range(len(columns)))
    print(header)
    print("-" * len(header))
    for row in rows:
        print(" | ".join(str(row[i]).ljust(widths[i]) for i in range(len(columns))))

    input("\nPress Enter to continue...")