from flask import Flask, request, jsonify
from flask_socketio import SocketIO
from flask_cors import CORS
import time
import uuid

app = Flask(__name__)
CORS(app, origins=["https://draw.partyshow.xyz"])
socketio = SocketIO(app, cors_allowed_origins=["https://draw.partyshow.xyz"])

names = []
draw_timer = None
draw_results = []


def broadcast_names():
    socketio.emit("update_names", names)


def draw_scheduler(draw_time):
    def wait_and_draw():
        delay = draw_time - time.time()
        if delay > 0:
            socketio.sleep(delay)

        shuffled = sorted(names, key=lambda _: uuid.uuid4().hex)
        global draw_results
        draw_results = shuffled
        socketio.emit("draw_result", shuffled)
        broadcast_names()

    socketio.start_background_task(wait_and_draw)


@app.route("/admin/reset", methods=["POST"])
def admin_reset():
    global names, draw_timer
    data = request.json
    draw_time = data.get("draw_time")  # should be a float (epoch seconds)

    if not draw_time:
        return jsonify({"error": "Missing draw_time"}), 400

    names = []
    draw_timer = float(draw_time)
    draw_scheduler(draw_timer)
    broadcast_names()
    socketio.emit("draw_time", draw_timer)  # Emit draw time to clients
    return jsonify({"status": "reset", "draw_time": draw_time})


@socketio.on("connect")
def handle_connect():
    socketio.emit("draw_result", draw_results)
    socketio.emit("update_names", names)
    socketio.emit("draw_time", draw_timer)  # Emit draw time to the client


@socketio.on("register_name")
def handle_register(name):
    if not isinstance(name, str) or not name.strip():
        socketio.emit("error", {"message": "שם לא חוקי"})
        return
    if draw_timer is not None and time.time() >= draw_timer:
        socketio.emit("error", {"message": "ההרשמה נסגרה"})
        return
    if name in names:
        socketio.emit("error", {"message": "השם כבר רשום"})
        return

    names.append(name)
    broadcast_names()


@socketio.on("disconnect")
def handle_disconnect():
    pass  # nothing to clean up for now


if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5050, allow_unsafe_werkzeug=True)
