import getpass
import math
from datetime import datetime, timedelta


def get_password(prompt="Password: "):
    return getpass.getpass(prompt)

def get_current_ts():
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

def get_end_ts():
    return (datetime.now() + timedelta(days=365)).strftime('%Y-%m-%d %H:%M:%S')

def validate_card_number(card_str):
    digits = card_str.replace(" ", "")
    if digits.isdigit() and len(digits) == 16:
        return True, digits
    return False, None

def validate_cvv(cvv_str):
    s = cvv_str.strip()
    return s.isdigit() and len(s) == 3

def validate_expiry(expiry_str):
    try:
        parts = expiry_str.strip().split('/')
        if len(parts) != 2:
            return False
        month = int(parts[0])
        year = int(parts[1])
        if month < 1 or month > 12:
            return False
        now = datetime.now()
        if year > now.year:
            return True
        if year == now.year and month >= now.month:
            return True
        return False
    except (ValueError, IndexError):
        return False

def mask_card(card_no):
    s = str(card_no)
    return '*' * (len(s) - 4) + s[-4:]

def paginate(items, columns, allow_select=False, id_index=0, footer=None):
    if not items:
        print("\nNo records found.")
        return None

    page_size = 5
    total_pages = math.ceil(len(items) / page_size)
    page = 0

    while True:
        start = page * page_size
        end = min(start + page_size, len(items))
        page_items = items[start:end]
        widths = []
        for i in range(len(columns)):
            w = len(str(columns[i]))
            for row in page_items:
                if i < len(row):
                    w = max(w, len(str(row[i])))
            widths.append(w)
        header = " | ".join(str(columns[i]).ljust(widths[i]) for i in range(len(columns)))
        print("\n" + header)
        print("-" * len(header))
        for row in page_items:
            print(" | ".join(str(row[i]).ljust(widths[i]) for i in range(len(columns))))

        if footer:
            print(footer)

        print(f"\nPage {page + 1} of {total_pages}")

        options = []
        if page < total_pages - 1:
            options.append("N-Next")
        if page > 0:
            options.append("P-Prev")
        options.append("B-Back")

        if allow_select:
            prompt = f"[{', '.join(options)}] or enter ID to select: "
        else:
            prompt = f"[{', '.join(options)}]: "

        choice = input(prompt).strip()
        choice_upper = choice.upper()

        if choice_upper == 'N' and page < total_pages - 1:
            page += 1
        elif choice_upper == 'P' and page > 0:
            page -= 1
        elif choice_upper == 'B':
            return None
        elif allow_select and choice:
            found = None
            for row in items:
                if str(row[id_index]).strip() == choice.strip():
                    found = row
                    break
            if found:
                return found
            else:
                print("Invalid selection. Try again.")
        else:
            print("Invalid choice.")