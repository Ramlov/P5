# app.py
from flask import Flask, render_template, Response
import time

app = Flask(__name__)

def read_last_line():
    try:
        with open("log.txt", "r") as file:
            lines = file.readlines()
            if lines:
                return lines[-1].strip()
            else:
                return "No logs available."
    except Exception as e:
        return f"Error reading log file: {e}"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/stream')
def stream():
    def generate():
        while True:
            last_line = read_last_line()
            yield f"data: {last_line}\n\n"  # Format required for Server-Sent Events (SSE)
            time.sleep(0.5)
    return Response(generate(), mimetype='text/event-stream')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5556)