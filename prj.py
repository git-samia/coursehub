import sys
import sqlite3
from helpers import get_password
from student import student_menu
from instructor import instructor_menu
from admin import admin_menu


# Prompts the user for a uid and password, checks the uid exists in the database first,
# then verifies the password matches; allows retrying both uid and password separately
# and returns the user's uid, name, and role on success or None if the user goes back
def login(conn):
    while True:
        uid_input = input("Enter user ID (or 'b' to go back): ").strip()
        if uid_input.lower() == 'b':
            return None
        try:
            uid = int(uid_input)
        except ValueError:
            uid = uid_input
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM users WHERE uid = ?", (uid,))
        if not cur.fetchone():
            print("\nUser ID not found. Please try again.\n")
            continue
        while True:
            pwd = get_password("Enter password (or 'b' to go back): ")
            if pwd.lower() == 'b':
                break
            cur.execute("SELECT uid, name, role FROM users WHERE uid = ? AND pwd = ?", (uid, pwd))
            user = cur.fetchone()
            if user:
                print(f"\nWelcome, {user[1]}!")
                return {'uid': user[0], 'name': user[1], 'role': user[2]}
            else:
                print("\nIncorrect password. Please try again.\n")


# Collects name, email, and password from a new user, validates email format and
# uniqueness, generates a new uid by incrementing the current max uid, inserts the
# new user into the database with role Student, and returns the new user's details;
# returns None if the user chooses to go back at any point
def register(conn):
    while True:
        name = input("Enter name (or 'b' to go back): ").strip()
        if name.lower() == 'b':
            return None
        if not name:
            print("Name cannot be empty.")
            continue
        break
    while True:
        email = input("Enter email (or 'b' to go back): ").strip()
        if email.lower() == 'b':
            return None
        if not email or '@' not in email or '.' not in email.split('@')[-1] or len(email.split('.')[-1]) < 2:
            print("Invalid email format.")
            continue
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM users WHERE email = ?", (email,))
        if cur.fetchone():
            print("Email already in use. Please try again.")
            continue
        break
    while True:
        pwd = get_password("Enter password (or 'b' to go back): ")
        if pwd.lower() == 'b':
            return None
        if not pwd:
            print("Password cannot be empty.")
            continue
        break
    cur = conn.cursor()
    cur.execute("SELECT COALESCE(MAX(uid), 0) + 1 FROM users")
    new_uid = cur.fetchone()[0]
    cur.execute(
        "INSERT INTO users (uid, name, email, role, pwd) VALUES (?, ?, ?, 'Student', ?)",
        (new_uid, name, email, pwd)
    )
    conn.commit()
    print(f"\nRegistration successful! Your user ID is: {new_uid}")
    return {'uid': new_uid, 'name': name, 'role': 'Student'}


# Determines the logged-in user's role and calls the corresponding menu function;
# keeps looping until the user logs out or exits, then returns the result so the
# main loop knows whether to show the welcome screen again or terminate the program
def run_role_menu(conn, user):
    while True:
        role = user['role']
        if role == 'Student':
            result = student_menu(conn, user['uid'])
        elif role == 'Instructor':
            result = instructor_menu(conn, user['uid'])
        elif role == 'Admin':
            result = admin_menu(conn, user['uid'])
        else:
            print("Unknown role.")
            return 'logout'

        if result in ('logout', 'exit'):
            return result


# Entry point of the program; reads the database filename from the command line argument,
# opens a connection, and presents the welcome screen where users can login, register,
# or exit; closes the database connection cleanly when the program ends
def main():
    if len(sys.argv) < 2:
        print("Usage: python prj.py <database_file>")
        sys.exit(1)

    db_file = sys.argv[1]
    conn = sqlite3.connect(db_file)

    try:
        while True:
            print("\n========== Welcome ==========")
            print("1. Login")
            print("2. Register")
            print("3. Exit")

            choice = input("Enter choice: ").strip()

            if choice == '1':
                user = login(conn)
                if user:
                    result = run_role_menu(conn, user)
                    if result == 'exit':
                        break

            elif choice == '2':
                user = register(conn)
                if user:
                    result = run_role_menu(conn, user)
                    if result == 'exit':
                        break

            elif choice == '3':
                break

            else:
                print("Invalid choice.")
    finally:
        conn.close()
        print("Goodbye!")


if __name__ == '__main__':
    main()