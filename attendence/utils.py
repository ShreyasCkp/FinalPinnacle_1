# attendence/utils.py
from datetime import datetime

def calculate_status(check_in, settings):
    if check_in is None:
        return "LOP"  # or "Absent", depending on your logic

    check_in_time = settings.check_in_time  # assume this is datetime.time
    actual = datetime.combine(datetime.today(), check_in)

    scheduled = datetime.combine(datetime.today(), check_in_time)
    diff_minutes = (actual - scheduled).total_seconds() / 60

    if diff_minutes <= settings.grace_period:
        return "Present"
    elif diff_minutes <= settings.late_threshold:
        return "Late"
    else:
        return "Absent"
