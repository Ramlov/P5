# app.py
from flask import Flask, render_template, Response
import time

app = Flask(__name__)

def read_log_file():
    try:
        with open("log.txt", "r") as file:
            return file.read()
    except Exception as e:
        return f"Error reading log file: {e}"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/stream')
def stream():
    def generate():
        while True:
            log_data = read_log_file()
            yield f"data: {log_data}\n\n"  # Format required for Server-Sent Events (SSE)
            time.sleep(0.5)
    return Response(generate(), mimetype='text/event-stream')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=6001)