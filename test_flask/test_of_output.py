# my_script.py

import time

def generate_output():
    while True:
        # Simulate continuous output generation
        yield "Current timestamp: " + time.ctime()
        time.sleep(1)  # Wait for 1 second before generating the next output
