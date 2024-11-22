from flask import Flask, request
import time
import threading

app = Flask(__name__)
current_value = 0


@app.route("/update", methods=["POST"])
def update_value():
    global current_value
    new_value = request.json.get("new_value")
    if new_value is not None:
        current_value = new_value
    return {"current_value": current_value}


def incrementer():
    global current_value
    while True:
        print(current_value)
        current_value += 1
        time.sleep(1)


# Démarre le thread d'incrémentation
threading.Thread(target=incrementer, daemon=True).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)  # Exposer le port de l'API
