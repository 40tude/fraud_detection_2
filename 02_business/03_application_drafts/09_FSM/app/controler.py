import requests
import time


# -----------------------------------------------------------------------------
class Fsm:
    def __init__(self, url: str):
        """Initializes the Fsm with the given base URL for API requests."""
        self.url = url

    def _post_request(self, endpoint: str):
        """Sends a POST request to the specified endpoint and returns the JSON response."""
        try:
            response = requests.post(f"{self.url}/{endpoint}")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error: {e}")
            return None

    def _get_request(self, endpoint: str):
        """Sends a GET request to the specified endpoint and returns the JSON response."""
        try:
            response = requests.get(f"{self.url}/{endpoint}")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error: {e}")
            return None

    def init(self):
        """Initializes the machine state and resets the value to 0."""
        status = self._post_request("init")
        if status:
            print(f"Current message: {status['message']}")
            print(f"Current state: {status['state']}")
            print(f"Current value: {status['value']}")

    def start(self):
        """Starts the machine in RUNNING state, allowing the increment loop to begin."""
        status = self._post_request("start")
        if status:
            print(f"Current message: {status['message']}")
            print(f"Current state: {status['state']}")

    def pause(self):
        """Pauses the machine, stopping the increment temporarily."""
        status = self._post_request("pause")
        if status:
            print(f"Current message: {status['message']}")
            print(f"Current state: {status['state']}")

    def stop(self):
        """Stops the machine and resets the value to 0."""
        status = self._post_request("stop")
        if status:
            print(f"Current message: {status['message']}")
            print(f"Current state: {status['state']}")

    def get_val(self):
        """Retrieves the current incremented value from the machine."""
        status = self._get_request("get_val")
        if status:
            print(f"Current val: {status['value']}")

    def get_status(self):
        """Retrieves the current state of the machine."""
        status = self._get_request("get_status")
        if status:
            print(f"Current status: {status['state']}")


# -----------------------------------------------------------------------------
if __name__ == "__main__":
    fsm = Fsm("http://127.0.0.1:5000")

    # Initial status check
    fsm.get_status()
    fsm.init()
    fsm.get_val()

    # Start the machine and wait to see if value increments
    fsm.start()
    time.sleep(3)  # Increased sleep time to allow for increment
    fsm.get_val()

    # Pause and check the value
    fsm.pause()
    fsm.get_val()

    # Resume and check the value again
    fsm.start()
    time.sleep(3)  # Increased sleep time to allow for increment
    fsm.get_val()

    # Stop the machine and reset the value
    fsm.stop()
