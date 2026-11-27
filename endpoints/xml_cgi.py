from datetime import datetime


# True: enable the vulnerable training behavior.
# False: disable the alternate authentication path.
VULNERABLE = True

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "12345"


def generate_code_of_day():
    """
    Synthetic code-of-day algorithm for the local training lab.
    This is not the original Danfoss algorithm.
    """
    today = datetime.now()

    month = today.month + 1
    day = today.day * 4
    year = today.year % 100

    return f"{month:02d}{day:02d}{year:02d}{month:02d}"


def check_code_of_day(password):
    expected_code = generate_code_of_day()
    return password == expected_code


def read_date_time():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def getauth(
    username,
    password,
    auth_mode="",
    service_access=""
):
    """
    Authentication dispatcher.

    The alternate authentication parameters are synthetic.
    They model an authentication design flaw for local training.
    """

    # Normal authentication
    if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
        return "Connection granted"

    # Simulated alternate authentication path
    if (
        VULNERABLE
        and auth_mode == "service"
        and service_access == "enabled"
    ):
        if check_code_of_day(password):
            return "Connection granted"

    return "Connection refused"
