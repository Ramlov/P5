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

        # Stream each line, then remove it from the file
        with open('log.txt', 'w') as log_file:
            for line in lines:
                yield f"{line}<br>"
            # Write only unread lines back (in this case, nothing is written back to the file)

# Route to display the streamed log content
@app.route('/')
def stream_packets():
    return Response(generate_log(), content_type='text/html')

if __name__ == '__main__':
    app.run(debug=True, threaded=True, host='0.0.0.0', port=5005)
