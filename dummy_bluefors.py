import random
from datetime import datetime

class DummyBlueforsInstrument:
    """
    A dummy/simulated instrument for Bluefors refrigeration systems.
    This class mimics the interface of the real instrument (e.g., generating alerts,
    assembling state messages, receiving commands) so that it can be used in place of
    actual hardware for testing and development purposes.
    """
    def __init__(self, name="DummyBluefors"):
        # Assign a name for the instrument; useful for identification in logs and messages.
        self.name = name
        # Initialize the state dictionary with some example channels.
        # Values are strings "0", "1" or "2" to mimic 'off', 'on', and 'contradictory/unknown'
        self.state = {
            "pulsetube": "0",
            "turbo1": "0",
            "compressor": "0"
        }
        # Time of the last update
        self.last_update = datetime.now()

    def simulate_state_change(self):
        """
        Randomly simulate a change in the state channels.
        This method mimics the periodic updates of sensor values in the actual Bluefors instrument.
        """
        for channel in self.state.keys():
            # Randomly select a state: off ("0"), on ("1"), or error/uncertain ("2")
            self.state[channel] = random.choice(["0", "1", "2"])
        self.last_update = datetime.now()  # update the state timestamp

    def generate_alert_messages(self):
        """
        Generate alert messages based on current state values.
        This simulation checks the state dictionary against some simple conditions.
        """
        alerts = []
        # If 'pulsetube' is on, simulate an alert for manual start
        if self.state.get("pulsetube") == "1":
            alerts.append("Pulsetube manual start")
        # If 'compressor' is on, simulate a condensing script start alert
        if self.state.get("compressor") == "1":
            alerts.append("Condensing script started")
        # You can add additional conditions to mimic other event markers
        return alerts

    def generate_state_message(self):
        """
        Assemble and return a formatted state summary message.
        Similar to the original API, it includes timestamp and state icons.
        """
        # Define basic icon representations for states:
        # "0": Off (⚪️), "1": On (🔵), "2": Error/contradictory (🌕)
        icons = {"0": "⚪️", "1": "🔵", "2": "🌕"}
        # Build header message with instrument name and last update time.
        message = f"{self.name} state @ {self.last_update.strftime('%Y-%m-%d %H:%M:%S')}\n"
        # Append each channel and its corresponding icon.
        for channel, state in self.state.items():
            message += f"{channel}: {icons.get(state, '?')}  "
        return message.strip()

    def receive_signal(self, command):
        """
        Simulate receiving a command/signal that changes the instrument's state.
        The command can be a string like 'start pulsetube' or 'stop compressor'.
        """
        # Check the command and adjust state accordingly.
        if command == "start pulsetube":
            self.state["pulsetube"] = "1"
        elif command == "stop pulsetube":
            self.state["pulsetube"] = "0"
        elif command == "start compressor":
            self.state["compressor"] = "1"
        elif command == "stop compressor":
            self.state["compressor"] = "0"
        elif command == "start turbo1":
            self.state["turbo1"] = "1"
        elif command == "stop turbo1":
            self.state["turbo1"] = "0"
        else:
            # If command is unrecognized, simply return an info message.
            return f"Unrecognized command: {command}"
        # Update the timestamp each time a command is processed.
        self.last_update = datetime.now()
        return f"Command '{command}' executed at {self.last_update.strftime('%Y-%m-%d %H:%M:%S')}"

    def get_state(self):
        """
        Return the current state dictionary.
        This can be used for checking the instrument status programmatically.
        """
        return self.state

# Example usage of the dummy instrument.
if __name__ == "__main__":
    # Create an instance of the dummy Bluefors instrument.
    dummy_instrument = DummyBlueforsInstrument()

    # Print the initial state message.
    print(dummy_instrument.generate_state_message())

    # Simulate a command to start the pulsetube.
    response = dummy_instrument.receive_signal("start pulsetube")
    print(response)

    # Optionally, simulate a random state change (to mimic real-time updates).
    dummy_instrument.simulate_state_change()
    print(dummy_instrument.generate_state_message())

    # Generate and print any alert messages based on the current state.
    alerts = dummy_instrument.generate_alert_messages()
    print("Alert messages:", alerts)
