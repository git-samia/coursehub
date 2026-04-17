from helpers import get_current_ts


# Displays the admin menu and handles navigation to stats, logout, and exit.
def admin_menu(conn, uid):
    while True:
        print("\n========== Admin Menu ==========")
        print("1. Platform statistics")
        print("2. Logout")
        print("3. Exit")

        choice = input("Enter choice: ").strip()

        if choice == '1':
            platform_statistics(conn)
        elif choice == '2':
            return 'logout'
        elif choice == '3':
            return 'exit'
        else:
            print("Invalid choice.")


# Displays two reports: top 5 courses by active enrollment (ties at 5th included),
# and payment counts for all courses ordered highest first
def platform_statistics(conn):
    now = get_current_ts()
    cur = conn.cursor()

    cur.execute("""
        SELECT c.cid, c.title,
               (SELECT COUNT(*) FROM enrollments e
                WHERE e.cid = c.cid AND e.role = 'Student'
                AND e.start_ts <= ? AND e.end_ts >= ?) AS active_enrollment
        FROM courses c
        ORDER BY active_enrollment DESC
    """, (now, now))
    all_courses = cur.fetchall()

    print("\n========== Top 5 Courses by Active Enrollment ==========")
    print(f"{'cid':<10} | {'title':<40} | {'active_enrollment'}")
    print("-" * 70)

    if all_courses:
        if len(all_courses) <= 5:
            for row in all_courses:
                print(f"{str(row[0]):<10} | {str(row[1]):<40} | {row[2]}")
        else:
            fifth_count = all_courses[4][2]
            for row in all_courses:
                if row[2] >= fifth_count:
                    print(f"{str(row[0]):<10} | {str(row[1]):<40} | {row[2]}")
                else:
                    break
    else:
        print("No courses found.")

    cur.execute("""
        SELECT c.cid, c.title, COUNT(p.ts) AS payment_count
        FROM courses c
        LEFT JOIN payments p ON c.cid = p.cid
        GROUP BY c.cid, c.title
        ORDER BY payment_count DESC
    """)
    payments = cur.fetchall()

    print("\n========== Payment Counts per Course ==========")
    print(f"{'cid':<10} | {'title':<40} | {'payment_count'}")
    print("-" * 70)

    if payments:
        for row in payments:
            print(f"{str(row[0]):<10} | {str(row[1]):<40} | {row[2]}")
    else:
        print("No payment data found.")

    input("\nPress Enter to continue...")