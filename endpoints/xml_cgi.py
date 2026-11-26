
from datetime import datetime


def generate_code():
    today = datetime.now()

    month = today.month + 1
    day = today.day * 4
    year = today.year % 100

    return f"{month:02d}{day:02d}{year:02d}{month:02d}"


def read_date_time():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def getauth(username, password):
    # Daily code authentication
    if password == generate_code():
        return "Connection granted"

    # Default admin password
    elif username == "admin" and password == "12345":
        return "Connection granted"

    # Authentication refused
    return "Connection refused"

