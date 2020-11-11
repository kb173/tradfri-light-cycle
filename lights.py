import sys
import os

folder = os.path.dirname(os.path.abspath(__file__))  # noqa
sys.path.insert(0, os.path.normpath("%s/.." % folder))  # noqa

from pytradfri import Gateway
from pytradfri.api.libcoap_api import APIFactory
from pytradfri.error import PytradfriError
from pytradfri.error import RequestTimeout
from pytradfri.util import load_json, save_json
import json
import uuid
import argparse

import datetime
import csv
import time


CONFIG_FILE = "tradfri_standalone_psk.conf"

temperature_targets = {}
pause_time = 20

# Tradfri Gateway Connection
parser = argparse.ArgumentParser()
parser.add_argument(
    "host", metavar="IP", type=str, help="IP Address of your Tradfri gateway"
)
parser.add_argument(
    "-K",
    "--key",
    dest="key",
    required=False,
    help="Security code found on your Tradfri gateway",
)
args = parser.parse_args()


if args.host not in load_json(CONFIG_FILE) and args.key is None:
    print(
        "Please provide the 'Security Code' on the back of your " "Tradfri gateway:",
        end=" ",
    )
    key = input().strip()
    if len(key) != 16:
        raise PytradfriError("Invalid 'Security Code' provided.")
    else:
        args.key = key


conf = load_json(CONFIG_FILE)

try:
    identity = conf[args.host].get("identity")
    psk = conf[args.host].get("key")
    api_factory = APIFactory(host=args.host, psk_id=identity, psk=psk)
except KeyError:
    identity = uuid.uuid4().hex
    api_factory = APIFactory(host=args.host, psk_id=identity)

    try:
        psk = api_factory.generate_psk(args.key)
        print("Generated PSK: ", psk)

        conf[args.host] = {"identity": identity, "key": psk}
        save_json(CONFIG_FILE, conf)
    except AttributeError:
        raise PytradfriError(
            "Please provide the 'Security Code' on the "
            "back of your Tradfri gateway using the "
            "-K flag."
        )

api = api_factory.request

gateway = Gateway()

devices_command = gateway.get_devices()
devices_commands = api(devices_command)
devices = api(devices_commands)
lights = [dev for dev in devices if dev.has_light_control]

print(devices)

# Parse the temperature target CSV file
with open('temperatures.csv') as temperatures_csv:
    reader = csv.reader(temperatures_csv, delimiter=',')

    lines = []
    
    for row in reader:
        row_to_add = []
        
        for col in reader:
            row_to_add.append(col)
        
        lines += row_to_add
    
    num_entries = len(lines)
    
    for i in range(0, num_entries):
        current_time = datetime.datetime.strptime(lines[i][0], "%H:%M").time()
        current_temp = int(lines[i][1])
        
        next_i = (i + 1) % num_entries
        target_time = datetime.datetime.strptime(lines[next_i][0], "%H:%M").time()
        target_temp = int(lines[next_i][1])
        
        temperature_targets[(current_time, target_time)] = (current_temp, target_temp)


# Set all lights to the given temperature
def set_lights_temperature(temp):
    try:
        for light in lights:
            api(light.light_control.set_color_temp(temp))
    except RequestTimeout:
        print("Couldn't update temperature due to timeout...")
    
    print("Updated temperature to", temp)


# Convert a time like 12:15 to 12.25.
def time_to_float(t):
    return t.hour + t.minute / 60.0 + t.second / 3600.0


# We alternate between value and value+1, because there is an issue
#  with a light being turned off, getting a new value, turned on,
#  and getting the same value again
#  (https://github.com/home-assistant-libs/pytradfri/issues/270)
alternator = 0


# Main Loop
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
            
            set_lights_temperature(int(interpolated) + alternator)
    
    alternator = (alternator + 1) % 2
    time.sleep(pause_time)
