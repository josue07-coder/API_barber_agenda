from datetime import datetime, timedelta, time

def calculate_end_time(start_time: time, duration_minutes: int) -> time:
    start = datetime.combine(datetime.today(), start_time)
    end = start + timedelta(minutes=duration_minutes)
    return end.time()
