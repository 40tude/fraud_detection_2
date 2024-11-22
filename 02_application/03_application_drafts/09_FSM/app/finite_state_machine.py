from flask import Flask, jsonify
import threading
import time


# -----------------------------------------------------------------------------
app = Flask(__name__)
value = 0
state = "INIT"
stop_event = threading.Event()


# -----------------------------------------------------------------------------
# Threaded loop function
def increment_loop():
    global value, state
    while not stop_event.is_set():
        if state == "RUNNING":
            value += 1
            # print(f"Incrementing value, current value = {value}", flush=True)
            time.sleep(1)
        else:
            # print("Loop waiting, state is not RUNNING", flush=True)
            time.sleep(0.1)


# -----------------------------------------------------------------------------
@app.route("/init", methods=["POST"])
def init():
    global value, state
    value = 0
    state = "INIT"
    return jsonify({"message": "Initialized", "state": state, "value": value})


# -----------------------------------------------------------------------------
@app.route("/start", methods=["POST"])
def start():
    global state
    if state != "RUNNING":
        state = "RUNNING"
        print("State changed to RUNNING", flush=True)
    return jsonify({"message": "Started", "state": state})


# -----------------------------------------------------------------------------
@app.route("/pause", methods=["POST"])
def pause():
    global state
    state = "PAUSED"
    return jsonify({"message": "Paused", "state": state})


# -----------------------------------------------------------------------------
@app.route("/stop", methods=["POST"])
def stop():
    global state
    state = "STOPPED"
    return jsonify({"message": "Stopped", "state": state})


# -----------------------------------------------------------------------------
@app.route("/get_val", methods=["GET"])
def get_val():
    return jsonify({"value": value})


# -----------------------------------------------------------------------------
@app.route("/get_status", methods=["GET"])
def get_status():
    return jsonify({"state": state})


# -----------------------------------------------------------------------------
if __name__ == "__main__":
    loop_thread = threading.Thread(target=increment_loop, daemon=True)
    loop_thread.start()
    print("Increment loop thread started", flush=True)

    # When you configure your Flask application to listen on 127.0.0.1, this means it will only accept connections from the same machine.
    # No other machine or Docker container will be able to connect to your application via this address.
    # This is fine for local development, but if you're running your application in a Docker container, or if you want other machines to connect to your application, this poses a problem.
    # app.run(host="127.0.0.1", port=5000, debug=True)   # when NOT in docker

    # This means that the application will listen on all available network interfaces.
    # In other words, it will accept connections from any IP address, including those of other Docker containers or machines on the local network.
    # By using 0.0.0.0, you enable your application to be accessible from the outside, which is essential when you're running the application in a Docker container and want to access it from the host or other containers.
    app.run(host="0.0.0.0", port=5000)  # in docker
