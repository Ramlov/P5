from flask import Flask, Response
import time

app = Flask(__name__)

def generate_log():
    with open('log.txt', 'r') as log_file:
        while True:
            # Read the new line from the file
            line = log_file.readline()
            if not line:
                # If no new lines, wait and continue
                time.sleep(0.1)
                continue
            yield f"{line}<br>"

# Route to display the streamed log content


@app.route('/stream-packets')
def stream_packets():
    return Response(generate_log(), content_type='text/html')


if __name__ == '__main__':
    app.run(debug=True, threaded=True)