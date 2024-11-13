from flask import Flask, Response
import time

app = Flask(__name__)

# Function to stream log file content, keeping only the last 20 lines
def generate_log():
    while True:
        with open('log.txt', 'r+') as log_file:
            # Read all lines from the file
            lines = log_file.readlines()

            # Keep only the last 20 lines
            if len(lines) > 20:
                lines = lines[-20:]

            # Rewind the file and truncate it to remove old content
            log_file.seek(0)
            log_file.truncate()

            # Write the latest 20 lines back to the file
            log_file.writelines(lines)

            # Join the lines into a plain text string to return
            yield ''.join(lines)

            time.sleep(0.1)

# Route to display the streamed log content
@app.route('/stream-packets')
def stream_packets():
    return Response(generate_log(), content_type='text/plain')

if __name__ == '__main__':
    app.run(debug=True, threaded=True, port=5002, host='0.0.0.0')