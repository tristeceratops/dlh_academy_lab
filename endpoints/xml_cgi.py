from datetime import datetime


def read_date_time():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

