from helpers import (get_current_ts, get_end_ts, validate_card_number,
                     validate_cvv, validate_expiry, mask_card, paginate)


def student_menu(conn, uid):
    while True:
        print("\n========== Student Menu ==========")
        print("1. Search for courses")
        print("2. View enrolled courses")
        print("3. View past payments")
        print("4. Logout")
        print("5. Exit")

        choice = input("Enter choice: ").strip()

        if choice == '1':
            search_courses(conn, uid)
        elif choice == '2':
            view_enrolled_courses(conn, uid)
        elif choice == '3':
            view_past_payments(conn, uid)
        elif choice == '4':
            return 'logout'
        elif choice == '5':
            return 'exit'
        else:
            print("Invalid choice.")


def search_courses(conn, uid):
    while True:
        keyword = input("\nEnter search keyword (or 'b' to go back): ").strip()
        if keyword.lower() == 'b':
            return
        category = input("Filter by category (leave blank for all): ").strip()
        min_price = input("Min price (leave blank for none): ").strip()
        max_price = input("Max price (leave blank for none): ").strip()
        base_query = """
            SELECT c.cid, c.title, c.description, c.category, c.price,
                   c.pass_grade, c.max_students,
                   (SELECT COUNT(*) FROM enrollments e
                    WHERE e.cid = c.cid AND e.role = 'Student'
                    AND e.start_ts <= ? AND e.end_ts >= ?) AS current_enrollment
            FROM courses c
            WHERE (LOWER(c.title) LIKE ? OR LOWER(c.description) LIKE ?)
        """
        while True:
            now = get_current_ts()
            params = [now, now, f'%{keyword.lower()}%', f'%{keyword.lower()}%']
            query = base_query
            if category:
                query += " AND LOWER(c.category) = LOWER(?)"
                params.append(category)
            if min_price:
                try:
                    query += " AND c.price >= ?"
                    params.append(float(min_price))
                except ValueError:
                    print("Invalid min price.")
                    break
            if max_price:
                try:
                    query += " AND c.price <= ?"
                    params.append(float(max_price))
                except ValueError:
                    print("Invalid max price.")
                    break
            cur = conn.cursor()
            cur.execute(query, params)
            results = cur.fetchall()
            columns = ['cid', 'title', 'description', 'category', 'price',
                        'pass_grade', 'max_students', 'current_enrollment']
            selected = paginate(results, columns, allow_select=True, id_index=0)
            if selected:
                result = view_course_details(conn, uid, selected[0])
                if result == 'enrolled':
                    break  # break inner loop → back to search prompt
            else:
                break  # B pressed → back to search prompt


def view_course_details(conn, uid, cid):
    now = get_current_ts()
    cur = conn.cursor()

    cur.execute("""
        SELECT c.cid, c.title, c.description, c.category, c.price,
               c.pass_grade, c.max_students,
               (SELECT COUNT(*) FROM enrollments e
                WHERE e.cid = c.cid AND e.role = 'Student'
                AND e.start_ts <= ? AND e.end_ts >= ?) AS current_enrollment
        FROM courses c WHERE c.cid = ?
    """, (now, now, cid))

    course = cur.fetchone()
    if not course:
        print("Course not found.")
        return

    labels = ['cid', 'title', 'description', 'category', 'price',
              'pass_grade', 'max_students', 'current_enrollment']
    print("\n========== Course Details ==========")
    for i, label in enumerate(labels):
        print(f"  {label}: {course[i]}")

    cur.execute("""
        SELECT 1 FROM enrollments
        WHERE cid = ? AND uid = ? AND role = 'Student'
        AND start_ts <= ? AND end_ts >= ?
    """, (cid, uid, now, now))

    if cur.fetchone():
        print("\nYou are already enrolled in this course.")
    else:
        choice = input("\nWould you like to enroll? (y/n): ").strip().lower()
        if choice == 'y':
            enroll_in_course(conn, uid, cid, course)
            return 'enrolled'


def enroll_in_course(conn, uid, cid, course):
    now = get_current_ts()
    cur = conn.cursor()
    cur.execute("""
        SELECT COUNT(*) FROM enrollments
        WHERE cid = ? AND role = 'Student'
        AND start_ts <= ? AND end_ts >= ?
    """, (cid, now, now))
    current = cur.fetchone()[0]
    if current >= course[6]:
        print("This course is full. Cannot enroll.")
        return
    while True:
        card_input = input("Enter credit card number (16 digits, or 'b' to cancel): ").strip()
        if card_input.lower() == 'b':
            return
        valid, card_no = validate_card_number(card_input)
        if valid:
            break
        print("Invalid card number. Must be 16 digits.")
    while True:
        cvv = input("Enter CVV (3 digits, or 'b' to cancel): ").strip()
        if cvv.lower() == 'b':
            return
        if validate_cvv(cvv):
            break
        print("Invalid CVV. Must be 3 digits.")
    while True:
        expiry = input("Enter expiry date (MM/YYYY, or 'b' to cancel): ").strip()
        if expiry.lower() == 'b':
            return
        if validate_expiry(expiry):
            break
        print("Invalid or expired expiry date.")
    start_ts = now
    end_ts = get_end_ts()
    cur.execute("""
        INSERT INTO enrollments (cid, uid, start_ts, end_ts, role)
        VALUES (?, ?, ?, ?, 'Student')
    """, (cid, uid, start_ts, end_ts))
    cur.execute("""
        INSERT INTO payments (uid, cid, ts, credit_card_no, expiry_date)
        VALUES (?, ?, ?, ?, ?)
    """, (uid, cid, start_ts, card_no, expiry))
    conn.commit()
    print("\n========== Enrollment Confirmation ==========")
    print(f"  cid: {cid}")
    print(f"  title: {course[1]}")
    print(f"  price: {course[4]}")
    print(f"  ts: {start_ts}")
    print(f"  card: {mask_card(card_no)}")
    input("\nPress Enter to continue...")



def view_enrolled_courses(conn, uid):
    while True:
        now = get_current_ts()
        cur = conn.cursor()

        cur.execute("""
            SELECT c.cid, c.title, c.category, e.start_ts, c.pass_grade
            FROM enrollments e
            JOIN courses c ON e.cid = c.cid
            WHERE e.uid = ? AND e.role = 'Student'
            AND e.start_ts <= ? AND e.end_ts >= ?
        """, (uid, now, now))

        courses = cur.fetchall()
        columns = ['cid', 'title', 'category', 'start_ts', 'pass_grade']

        selected = paginate(courses, columns, allow_select=True, id_index=0)
        if selected:
            course_options_menu(conn, uid, selected[0])
        else:
            return


def course_options_menu(conn, uid, cid):
    while True:
        print(f"\n========== Course {cid} Options ==========")
        print("1. See all modules")
        print("2. See grades")
        print("3. See certificate")
        print("4. Back")

        choice = input("Enter choice: ").strip()

        if choice == '1':
            see_modules(conn, uid, cid)
        elif choice == '2':
            see_grades(conn, uid, cid)
        elif choice == '3':
            see_certificate(conn, uid, cid)
        elif choice == '4':
            return
        else:
            print("Invalid choice.")


def see_modules(conn, uid, cid):
    cur = conn.cursor()
    cur.execute("""
        SELECT mid, name, weight, summary
        FROM modules WHERE cid = ?
    """, (cid,))
    modules = cur.fetchall()
    columns = ['mid', 'name', 'weight', 'summary']

    while True:
        selected = paginate(modules, columns, allow_select=True, id_index=0)
        if selected:
            see_lessons(conn, uid, cid, selected[0])
        else:
            return


def see_lessons(conn, uid, cid, mid):
    columns = ['lid', 'title', 'duration', 'status']

    while True:
        cur = conn.cursor()
        cur.execute("""
            SELECT l.lid, l.title, l.duration,
                   CASE WHEN EXISTS (
                       SELECT 1 FROM completion c
                       WHERE c.uid = ? AND c.cid = ? AND c.mid = ? AND c.lid = l.lid
                   ) THEN 'Completed' ELSE 'Not Completed' END AS status
            FROM lessons l
            WHERE l.cid = ? AND l.mid = ?
        """, (uid, cid, mid, cid, mid))
        lessons = cur.fetchall()

        selected = paginate(lessons, columns, allow_select=True, id_index=0)
        if selected:
            view_lesson_detail(conn, uid, cid, mid, selected[0])
        else:
            return


def view_lesson_detail(conn, uid, cid, mid, lid):
    cur = conn.cursor()
    cur.execute("""
        SELECT l.cid, l.mid, l.lid, l.title, l.duration, l.content,
               CASE WHEN EXISTS (
                   SELECT 1 FROM completion c
                   WHERE c.uid = ? AND c.cid = l.cid AND c.mid = l.mid AND c.lid = l.lid
               ) THEN 'Completed' ELSE 'Not Completed' END AS status
        FROM lessons l
        WHERE l.cid = ? AND l.mid = ? AND l.lid = ?
    """, (uid, cid, mid, lid))

    lesson = cur.fetchone()
    if not lesson:
        print("Lesson not found.")
        return

    labels = ['cid', 'mid', 'lid', 'title', 'duration', 'content', 'status']
    print("\n========== Lesson Details ==========")
    for i, label in enumerate(labels):
        print(f"  {label}: {lesson[i]}")

    if lesson[6] == 'Completed':
        print("\nThis lesson is already completed.")
    else:
        mark = input("\nMark as complete? (y/n): ").strip().lower()
        if mark == 'y':
            now = get_current_ts()
            cur.execute("""
                INSERT INTO completion (uid, cid, mid, lid, ts)
                VALUES (?, ?, ?, ?, ?)
            """, (uid, cid, mid, lid, now))
            conn.commit()
            print("Lesson marked as completed!")
    
    input("\nPress Enter to continue...")


def see_grades(conn, uid, cid):
    cur = conn.cursor()
    cur.execute("""
        SELECT g.mid, m.name, m.weight, g.grade, g.received_ts
        FROM grades g
        JOIN modules m ON g.cid = m.cid AND g.mid = m.mid
        WHERE g.uid = ? AND g.cid = ?
    """, (uid, cid))

    grades = cur.fetchall()

    if not grades:
        print("\nNo grades available.")
        print("final_grade = N/A")
        input("\nPress Enter to continue...")
        return

    cur.execute("""
        SELECT SUM(g.grade * m.weight) / SUM(m.weight)
        FROM grades g
        JOIN modules m ON g.cid = m.cid AND g.mid = m.mid
        WHERE g.uid = ? AND g.cid = ?
    """, (uid, cid))
    result = cur.fetchone()
    fg = result[0] if result and result[0] is not None else None

    if fg is not None:
        footer_text = f"\nfinal_grade = {fg:.2f}"
    else:
        footer_text = "\nfinal_grade = N/A"

    columns = ['mid', 'module_name', 'weight', 'grade', 'received_ts']
    paginate(grades, columns, footer=footer_text)


def see_certificate(conn, uid, cid):
    cur = conn.cursor()
    cur.execute("""
        SELECT cert.cid, c.title, cert.received_ts, cert.final_grade
        FROM certificates cert
        JOIN courses c ON cert.cid = c.cid
        WHERE cert.uid = ? AND cert.cid = ?
    """, (uid, cid))

    cert = cur.fetchone()

    if not cert:
        print("\nNo certificate found.")
    else:
        print("\n========== Certificate ==========")
        print(f"  cid: {cert[0]}")
        print(f"  course_title: {cert[1]}")
        print(f"  received_ts: {cert[2]}")
        print(f"  final_grade: {cert[3]}")

    input("\nPress Enter to continue...")


def view_past_payments(conn, uid):
    cur = conn.cursor()
    cur.execute("""
        SELECT p.ts, p.cid, c.title, p.credit_card_no, p.expiry_date
        FROM payments p
        JOIN courses c ON p.cid = c.cid
        WHERE p.uid = ?
        ORDER BY p.ts DESC
    """, (uid,))

    payments = cur.fetchall()

    masked = []
    for p in payments:
        masked.append((p[0], p[1], p[2], mask_card(str(p[3])), p[4]))

    columns = ['ts', 'cid', 'course_title', 'card_number', 'expiry_date']
    paginate(masked, columns)