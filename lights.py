import datetime
import csv
import time

temperature_targets = {}
pause_time = 5

with open('temperatures.csv') as temperatures_csv:
    reader = csv.reader(temperatures_csv, delimiter=',')

    lines = []
    
    for row in reader:
        row_to_add = []
        
        for col in reader:
            row_to_add.append(col)
        
        lines += row_to_add
    
    num_entries = len(lines)
    
    print(lines)
    
    for i in range(0, num_entries):
        current_time = datetime.datetime.strptime(lines[i][0], "%H:%M").time()
        current_temp = int(lines[i][1])
        
        next_i = (i + 1) % num_entries
        target_time = datetime.datetime.strptime(lines[next_i][0], "%H:%M").time()
        target_temp = int(lines[next_i][1])
        
        temperature_targets[(current_time, target_time)] = (current_temp, target_temp)

def time_to_float(t):
    return t.hour + t.minute / 60.0

while(True):
    current_time = datetime.datetime.now().time()

    for (begin, end), (temp_begin, temp_end) in temperature_targets.items():
        if current_time > begin and current_time < end:
            # Interpolate
            floatime = time_to_float(current_time)
            start = time_to_float(begin)
            target = time_to_float(end)
            
            t = (floatime - start) / (target - start)
            interpolated = temp_begin + (temp_end - temp_begin) * t
            
            print(interpolated)
    
    time.sleep(pause_time)
