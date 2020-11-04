from datetime import datetime
from datetime import time

temperature_targets = {
    (time(5, 00), time(20, 00)): (250, 250),
    (time(20, 00), time(21, 00)): (250, 300),
    (time(21, 00), time(00, 00)): (300, 400),
    (time(00, 00), time(2, 00)): (400, 450)
}

def time_to_float(t):
    return t.hour + t.minute / 60.0

current_time = datetime.now().time()

for (begin, end), (temp_begin, temp_end) in temperature_targets.items():
    if current_time > begin and current_time < end:
        # Interpolate
        floatime = time_to_float(current_time)
        start = time_to_float(begin)
        target = time_to_float(end)
        
        t = (floatime - start) / (target - start)
        interpolated = temp_begin + (temp_end - temp_begin) * t
        
        print(interpolated)
