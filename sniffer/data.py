# output_generator.py
import time
import random

def generate_output():
    while True:
        yield f"Current value: {random.randint(1, 100)}\n"
        time.sleep(1)  # Pause for a second
