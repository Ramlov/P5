from flask import Flask, Response
import time

app = Flask(__name__)

log_lines = []

def generate_log():
    global log_lines
    with open('log.txt', 'r') as log_file:
        while True:
            line = log_file.readline()
            if not line:
                # If no new lines, wait and continue
                time.sleep(0.1)
                continue
            # Append the new line to the list
            log_lines.append(line.strip())
            # Keep only the last 5 lines
            if len(log_lines) > 20:
                log_lines.pop(0)
            # Yield the current lines as HTML
            yield render_log_as_html()

def render_log_as_html():
    # Format the log lines as HTML
    return '<h1>Stream Packets</h1>' + ''.join(f"<p>{line}</p>" for line in log_lines)

# Route to display the streamed log content
@app.route('/stream-packets')
def stream_packets():
    return Response(generate_log(), content_type='text/html')

if __name__ == '__main__':
    app.run(debug=True, threaded=True, host='0.0.0.0', port=5124)