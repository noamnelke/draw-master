import argparse
from flask import Flask, request, jsonify
from flask_socketio import SocketIO
from flask_cors import CORS
import time
import uuid

app = Flask(__name__)

def parse_args():
    parser = argparse.ArgumentParser(description="Run the Flask app.")
    parser.add_argument(
        "--dev", action="store_true", help="Run in development mode with permissive CORS policy."
    )
    return parser.parse_args()

args = parse_args()

if args.dev:
    CORS(app, origins="*")
    socketio = SocketIO(app, cors_allowed_origins="*")
else:
    CORS(app, origins=["https://draw.partyshow.xyz", "https://draw-master.pages.dev"])
    socketio = SocketIO(app, cors_allowed_origins=["https://draw.partyshow.xyz", "https://draw-master.pages.dev"])

# Store entries as a dict where name is the key and token is the value
entries = {}  # Format: {"name": "token"}
draw_timer = None
draw_results = []


def broadcast_names():
    # Extract just the names for broadcasting to all clients
    names = list(entries.keys())
    socketio.emit("update_names", names)


def draw_scheduler(draw_time):
    def wait_and_draw():
        delay = draw_time - time.time()
        if delay > 0:
            socketio.sleep(delay)

        # Extract names for the draw
        names = list(entries.keys())
        shuffled = sorted(names, key=lambda _: uuid.uuid4().hex)
        global draw_results
        draw_results = shuffled
        socketio.emit("draw_result", shuffled)
        broadcast_names()

    socketio.start_background_task(wait_and_draw)


@app.route("/admin/reset", methods=["POST"])
def admin_reset():
    global entries, draw_timer
    data = request.json
    draw_time = data.get("draw_time")  # should be a float (epoch seconds)

    if not draw_time:
        return jsonify({"error": "Missing draw_time"}), 400

    entries = {}
    draw_timer = float(draw_time)
    draw_scheduler(draw_timer)
    broadcast_names()
    socketio.emit("draw_time", draw_timer)  # Emit draw time to clients
    return jsonify({"status": "reset", "draw_time": draw_time})


@socketio.on("connect")
def handle_connect():
    # Send current draw results
    socketio.emit("draw_result", draw_results, room=request.sid)
    
    # Extract just the names for broadcasting
    names = list(entries.keys())
    socketio.emit("update_names", names, room=request.sid)
    socketio.emit("draw_time", draw_timer, room=request.sid)  # Emit draw time to the client


@socketio.on("register_name")
def handle_register(name):
    if not isinstance(name, str) or not name.strip():
        socketio.emit("error", {"message": "שם לא חוקי"}, room=request.sid)
        return
    if draw_timer is not None and time.time() >= draw_timer:
        socketio.emit("error", {"message": "ההרשמה נסגרה"}, room=request.sid)
        return
    
    # Check if name already exists
    if name in entries:
        socketio.emit("error", {"message": "השם כבר רשום"}, room=request.sid)
        return

    # Generate a deletion token
    token = uuid.uuid4().hex
    
    # Add name with deletion token
    entries[name] = token
    
    # Send back the deletion token to this client only using their socket ID
    socketio.emit("registration_success", {"name": name, "token": token}, room=request.sid)
    
    # Broadcast updated name list to all clients
    broadcast_names()


@socketio.on("delete_name")
def handle_delete(data):
    if not isinstance(data, dict) or "name" not in data or "token" not in data:
        socketio.emit("error", {"message": "נתונים חסרים"}, room=request.sid)
        return
    
    name = data["name"]
    token = data["token"]
    
    if draw_timer is not None and time.time() >= draw_timer:
        socketio.emit("error", {"message": "ההרשמה כבר נסגרה"}, room=request.sid)
        return
    
    # Find the entry with the matching name and token
    if name in entries and entries[name] == token:
        # Found a match, remove it
        del entries[name]
        socketio.emit("delete_success", {"name": name}, room=request.sid)
        broadcast_names()
        return
    
    # If we get here, no match was found
    socketio.emit("error", {"message": "לא נמצא הרישום או שהקוד לא תקין"}, room=request.sid)


@socketio.on("disconnect")
def handle_disconnect():
    pass  # nothing to clean up for now


if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5050, allow_unsafe_werkzeug=True)
