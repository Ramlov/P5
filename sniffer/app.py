# app.py
from flask import Flask, render_template, Response
from data import generate_output
from sniff import sniff_packets

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/stream')
def stream():
    def generate():
        for line in sniff_packets():
            yield f"data: {line}\n\n"  # Format required for Server-Sent Events (SSE)
    return Response(generate(), mimetype='text/event-stream')

if __name__ == '__main__':
    app.run(debug=True)
