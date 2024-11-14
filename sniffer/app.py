from flask import Flask, Response
import time
import os

app = Flask(__name__)

# Track the last line index processed
last_line_index = 0

def generate_log():
    global last_line_index  # Use a global variable to track last line read

    while True:
        with open('log.txt', 'r') as log_file:
            lines = log_file.readlines()

        # If no new lines have been added, wait and continue
        if last_line_index >= len(lines):
            time.sleep(0.1)
            continue

        # Get only the new lines since last read
        new_lines = lines[last_line_index:]
        last_line_index = len(lines)  # Update index to the latest line

        # Stream each new line
        for line in new_lines:
            yield f"{line}<br>"

        # Keep only the last 6 lines in the log file
        with open('log.txt', 'w') as log_file:
            lines_to_keep = lines[-6:] if len(lines) > 6 else lines
            log_file.writelines(lines_to_keep)

        # Adjust the last line index if lines were trimmed
        last_line_index = max(0, last_line_index - (len(lines) - len(lines_to_keep)))

        # Brief pause to avoid excessive CPU usage
        time.sleep(0.1)

# Route to display the streamed log content
@app.route('/')
def stream_packets():
    return Response(generate_log(), content_type='text/html')

if __name__ == '__main__':
    app.run(debug=True, threaded=True, host='0.0.0.0', port=5005)
