# app.py

from flask import Flask, Response, render_template_string
from test_of_output import generate_output

app = Flask(__name__)

@app.route('/')
def home():
    # HTML template with JavaScript to listen for server-sent events
    html_template = """
    <!doctype html>
    <html lang="en">
      <head>
        <meta charset="utf-8">
        <title>Live Script Output</title>
      </head>
      <body>
        <h1>Live Output of the Script</h1>
        <div id="output"></div>
        <script>
          const outputDiv = document.getElementById('output');
          const evtSource = new EventSource('/stream');

          evtSource.onmessage = function(event) {
            // Append each new message to the output div
            outputDiv.innerHTML += '<p>' + event.data + '</p>';
          };
        </script>
      </body>
    </html>
    """
    return render_template_string(html_template)

@app.route('/stream')
def stream():
    # Use Flask's Response with the `generate_output` function
    return Response(event_stream(), mimetype="text/event-stream")

def event_stream():
    for output in generate_output():
        yield f"data: {output}\n\n"

if __name__ == '__main__':
    app.run(debug=True, threaded=True)
