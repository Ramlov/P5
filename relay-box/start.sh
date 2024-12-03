#!/bin/bash

# Navigate to the directory
cd /home/pi/P5/relay-box/sniffer

# Start the first program and log output
echo "Starting app.py..."
sudo python3 app.py >> /home/pi/log_app.txt 2>&1 &
APP_PID=$!

# Start the second program and log output
echo "Starting sniff.py..."
sudo python3 sniff.py >> /home/pi/log_sniff.txt 2>&1 &
SNIFF_PID=$!

# Save the process IDs
echo "app.py PID: $APP_PID"
echo "sniff.py PID: $SNIFF_PID"

