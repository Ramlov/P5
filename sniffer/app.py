from flask import Flask, Response
import time
import os

app = Flask(__name__)

def generate_log():
    while True:
        with open('log.txt', 'r') as log_file:
            lines = log_file.readlines()

        if not lines:
            # If no new lines, wait and continue
            time.sleep(0.1)
            continue

        # Stream each line, then keep only the last 6 lines in the file
        with open('log.txt', 'w') as log_file:
            # Retain only the last 6 lines in log.txt
            lines_to_keep = lines[-6:] if len(lines) > 6 else lines
            log_file.writelines(lines_to_keep)

        # Stream the new lines (all lines in this example)
        for line in lines_to_keep:
            yield f"{line}<br>"

        # Brief pause before the next check to avoid excessive CPU usage
        time.sleep(0.1)

# Route to display the streamed log content
@app.route('/')
def stream_packets():
    return Response(generate_log(), content_type='text/html')

if __name__ == '__main__':
    app.run(debug=True, threaded=True, host='0.0.0.0', port=5005)
