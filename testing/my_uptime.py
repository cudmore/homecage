import time
from datetime import timedelta

with open('/proc/uptime', 'r') as f:
    uptime_seconds = float(f.readline().split('.')[0])
    uptime_microseconds = timedelta(seconds = uptime_seconds).microseconds
    uptime_string = str(timedelta(seconds = uptime_seconds))

print(uptime_string)

now = time.time()
