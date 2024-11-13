from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import time
import threading

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

# Function to watch for new log data
def tail_log_file():
    with open('log.txt', 'r') as f:
        f.seek(0, 2)  # Move to end of file
        while True:
            line = f.readline()
            if not line:
                time.sleep(0.5)  # No new line; wait and check again
                continue
            # Emit the new line to connected clients
            socketio.emit('log_update', {'data': line}, broadcast=True)

# Start watching the log file in a background thread
threading.Thread(target=tail_log_file, daemon=True).start()

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=12345)
