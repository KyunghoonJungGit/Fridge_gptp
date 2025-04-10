class DummyBlueforsSlave:
    """
    A dummy simulator class mimicking the BlueforsSlave class of a Bluefors cryogenic system.
    
    This simulator reproduces key features of the Bluefors control system:
    - Tracking the states of various components (compressor, turbo pump, pulse tube, valves, heat switches, etc).
    - Simulating sensor readings (temperature sensors, compressor water temperatures, vacuum pressures).
    - Logging state changes with timestamps, maintaining a history of state transitions.
    - Detecting known event patterns from state changes and generating alert messages for them.
    - Producing a summary state message similar to the real system's `generate_state_message`.
    
    The class can operate entirely in-memory or optionally write logs to CSV files (in a specified directory) to emulate the Bluefors log files.
    If a log directory is given, the simulator will create daily subdirectories and log files for state changes ("Channels"), 
    status readings ("Status"), and pressure readings ("maxigauge") in CSV format.
    
    Methods are provided to control the simulated system (toggle or set component states), 
    which automatically log changes and update sensor readings. The interface of this dummy class follows the real BlueforsSlave interface 
    so it can serve as a drop-in replacement for testing or development of monitoring dashboards.
    """
    
    # Known event patterns: map specific combinations of state changes to alert message strings.
    # These patterns correspond to typical procedures (cooldown, warmup, etc) and manual operations in a Bluefors system&#8203;:contentReference[oaicite:2]{index=2}&#8203;:contentReference[oaicite:3]{index=3}.
    EVENT_MARKERS = {
        frozenset({'hs-still': '1', 'hs-mc': '1', 'pulsetube': '1'}.items()): "Cooldown script started",
        frozenset({'ext': '0', 'pulsetube': '0', 'v13': '1', 'v9': '0', 'turbo1': '0'}.items()): "Warmup script started",
        frozenset({'pulsetube': '0', 'v13': '1', 'v9': '0', 'turbo1': '0'}.items()): "Warmup script started",
        frozenset({'pulsetube': '0'}.items()): "Pulsetube manual stop",
        frozenset({'pulsetube': '1'}.items()): "Pulsetube manual start",
        frozenset({'compressor': '1', 'v9': '1', 'v7': '1', 'v6': '1', 'v5': '1'}.items()): "Condensing script started"
    }
    
    def __init__(self, nickname, password, server_address, server_port, logs_path=None):
        """
        Initialize the DummyBlueforsSlave.
        
        Parameters:
            nickname (str): Dummy nickname for the slave (unused in simulation).
            password (str): Dummy password (unused).
            server_address (str): Dummy server address (unused).
            server_port (int): Dummy server port (unused).
            logs_path (str or None): Optional directory path to use for log file output. 
                                     If provided, logs will be written to CSV files in this directory 
                                     (with subdirectories per date). If None, all logs are kept in memory only.
        """
        import os
        from datetime import datetime
        
        # Store the log path and determine mode (file vs memory)
        self._logs_path = logs_path
        self._use_files = logs_path is not None
        if self._use_files:
            # Create base log directory if not exists
            os.makedirs(logs_path, exist_ok=True)
        
        # Define the component state dictionary with all relevant channels.
        # All states are represented as strings "0", "1", or "2" (0 = off, 1 = on, 2 = transitional state if applicable).
        # Initialize with default values (assuming system is off initially for simulation).
        self.state = {
            'scroll1': '0',    # Scroll pump 1 (vacuum pump)
            'scroll2': '0',    # Scroll pump 2
            'turbo1': '0',     # Turbo pump
            'compressor': '0', # Helium compressor for pulse tube
            'pulsetube': '0',  # Pulse tube cryocooler
            'ext': '0',        # "ext" (possibly exchange gas valve or external valve)
            'v5': '0', 'v6': '0', 'v7': '0', 'v9': '0', 'v13': '0',  # Gas-handling valves
            'hs-still': '0',   # Heat switch for Still
            'hs-mc': '0'       # Heat switch for Mixing Chamber
        }
        # Define a fixed ordering of state keys for consistent logging (optional, here alphabetical for simplicity)
        self._state_keys_order = list(self.state.keys())
        
        # Lists to store log history in memory
        self._state_log = []    # list of state entries (each entry as list of strings [date, time, ID, key1, val1, ...])
        self._status_log = []   # list of status entries (each entry as [date, time, key1, val1, key2, val2, ...])
        self._pressure_log = [] # list of pressure entries (each entry as [date, time, p1, p2, ..., p6])
        
        # Simulated sensor values (temperatures, etc.) to include in status.
        # We include a few temperature sensors (in Kelvin or Celsius depending on sensor):
        # For example: mixing chamber temp (K), still temp (K), and compressor water in/out temps (°C).
        self.sensors = {
            'mix_chamber': 300.0,  # mixing chamber temperature [K]
            'still': 300.0,        # still temperature [K]
            'platform': 300.0,     # an intermediate stage (e.g., 4K plate) temperature [K]
            'cptempwi': 20.0,      # compressor water inlet temperature [°C]
            'cptempwo': 20.0       # compressor water outlet temperature [°C]
        }
        # We also simulate the turbo controller status "tc400setspdatt" (1 if turbo at set speed, 0 if not).
        self.sensors['tc400setspdatt'] = 0
        
        # Simulated pressure readings for up to 6 channels (e.g., vacuum gauges).
        # Initialize with some baseline values (in mbar).
        self.pressures = [1.0e-3, 1.0e-3, 1.0e-3, 1.0e-3, 1.0e-3, 1.0e-3]
        
        # Initialize logs with the current state and readings (as the starting point).
        now = datetime.now()
        self._log_state(now)    # log initial state snapshot
        self._log_status(now)   # log initial status (sensor readings)
        self._log_pressures(now) # log initial pressure readings
        
        # Last event check time for alerts: set to current time so that previous events (before now) are not reported.
        self._last_event_check_time = now
    
    def _log_state(self, timestamp):
        """
        Internal helper to log the current state (all channels) with a timestamp.
        Writes to in-memory log (and file, if enabled) in CSV format.
        """
        import csv, os
        # Format timestamp into date and time strings
        date_str = timestamp.strftime("%d-%m-%y")
        time_str = timestamp.strftime("%H:%M:%S")
        # Construct the row: [date, time, ID, key1, val1, key2, val2, ...] 
        # We'll use an empty string for the third column (ID placeholder), since it's not used for parsing.
        row = [date_str, time_str, '']
        for key in self._state_keys_order:
            row.append(key)
            row.append(self.state[key])
        # Append to memory log
        self._state_log.append(row)
        # If file logging is enabled, write to CSV file in a dated subdirectory
        if self._use_files:
            date_dir = os.path.join(self._logs_path, date_str)
            os.makedirs(date_dir, exist_ok=True)
            state_filename = os.path.join(date_dir, "Channels.csv")
            # If file doesn't exist, write header (optional). The real system might not use headers; we'll omit header for fidelity.
            with open(state_filename, 'a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(row)
    
    def _log_status(self, timestamp):
        """
        Internal helper to log the current status readings (sensors/temperatures) with a timestamp.
        Writes to in-memory status log and optionally to a file.
        """
        import csv, os
        date_str = timestamp.strftime("%d-%m-%y")
        time_str = timestamp.strftime("%H:%M:%S")
        # Prepare a row [date, time, sensor_key1, value1, sensor_key2, value2, ...]
        row = [date_str, time_str]
        for key, value in self.sensors.items():
            # Format numeric values to a reasonable number of decimals for logging
            if isinstance(value, float):
                val_str = f"{value:.3f}"
            else:
                val_str = str(value)
            row.append(key)
            row.append(val_str)
        self._status_log.append(row)
        if self._use_files:
            date_dir = os.path.join(self._logs_path, date_str)
            os.makedirs(date_dir, exist_ok=True)
            status_filename = os.path.join(date_dir, "Status.csv")
            with open(status_filename, 'a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(row)
    
    def _log_pressures(self, timestamp):
        """
        Internal helper to log the current pressure readings (six channels) with a timestamp.
        Writes to the pressure log in memory (and file if enabled).
        """
        import csv, os
        date_str = timestamp.strftime("%d-%m-%y")
        time_str = timestamp.strftime("%H:%M:%S")
        # Row format: [date, time, p1, p2, ..., p6]
        # Ensure we have exactly 6 pressure values (pad with 0.0 if needed for safety).
        pressures = list(self.pressures)[:6]
        pressures += [0.0] * (6 - len(pressures))
        # Format to strings (scientific notation or float)
        formatted_pressures = [f"{p:.3e}" for p in pressures]
        row = [date_str, time_str] + formatted_pressures
        self._pressure_log.append(row)
        if self._use_files:
            date_dir = os.path.join(self._logs_path, date_str)
            os.makedirs(date_dir, exist_ok=True)
            pressure_filename = os.path.join(date_dir, "maxigauge.csv")
            with open(pressure_filename, 'a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(row)
    
    def get_state(self, depth=0):
        """
        Retrieve a past state entry from the state change log.
        
        Parameters:
            depth (int): 0 for the latest state, 1 for the state before that, and so on.
        
        Returns:
            list: The raw state log entry (as a list of strings [date, time, '', key1, val1, ...]) for the requested depth.
                  If the requested depth is beyond the available history, the oldest available entry is returned.
        """
        # depth 0 means last entry
        idx = -1 - depth
        if abs(idx) > len(self._state_log):
            idx = 0  # if depth is too large, give the earliest
        return self._state_log[idx]
    
    def dict_state(self, depth=0):
        """
        Get a past state entry as a dictionary of channel states, including the timestamp.
        
        Parameters:
            depth (int): 0 for the latest state (current state), 1 for the one before that, etc.
        
        Returns:
            dict: Dictionary with keys for each channel plus 'datetime', representing the state at that time.
        """
        from datetime import datetime
        raw_state = self.get_state(depth)
        # raw_state[0] = date (dd-mm-yy), raw_state[1] = time (HH:MM:SS)
        timestamp = datetime.strptime(raw_state[0] + " " + raw_state[1], "%d-%m-%y %H:%M:%S")
        # The state entries start from index 3 onward as key, value pairs
        state_items = raw_state[3:]
        # Convert list of [key, value, key, value, ...] into dict
        state_dict = {state_items[i]: state_items[i+1] for i in range(0, len(state_items), 2)}
        state_dict["datetime"] = timestamp
        return state_dict
    
    def get_status(self):
        """
        Get the latest status log entry.
        
        Returns:
            list: The last status entry as a list [date, time, sensor1, value1, sensor2, value2, ...].
        """
        if not self._status_log:
            return None
        return self._status_log[-1]
    
    def get_last_pressures(self):
        """
        Get the most recent pressure readings from the log.
        
        Returns:
            list: A list of the latest pressure values for all channels.
        """
        if not self._pressure_log:
            return None
        last_entry = self._pressure_log[-1]
        # last_entry format: [date, time, p1, p2, ..., p6] (all as strings)
        # Convert pressure strings to floats
        pressures = [float(p) for p in last_entry[2:]]
        return pressures
    
    def get_last_state_change(self):
        """
        Compute the most recent state change (difference between the latest state and the previous state).
        
        Returns:
            dict: A dictionary of the channels that changed in the last transition, with their new values, 
                  plus a 'change_time' key for the timestamp of the change.
        """
        from datetime import datetime
        if len(self._state_log) < 2:
            # No previous state to compare
            return {}
        depth = 0
        change = {}
        # Loop backward through history until finding a change with at least one channel difference (beyond time).
        while depth < len(self._state_log) - 1:
            last_state = {k: v for k, v in zip(self._state_keys_order, self._state_log[-1-depth][3::2])}
            prev_state = {k: v for k, v in zip(self._state_keys_order, self._state_log[-2-depth][3::2])}
            change = {k: last_state[k] for k in last_state if last_state[k] != prev_state.get(k)}
            if change:
                # We found a change (non-empty)
                # Also capture the time of this change
                timestamp_str = self._state_log[-1-depth][0] + " " + self._state_log[-1-depth][1]
                change_time = datetime.strptime(timestamp_str, "%d-%m-%y %H:%M:%S")
                change["change_time"] = change_time
                return change
            depth += 1
        return {}
    
    def generate_alert_messages(self):
        """
        Check recent state changes for any known event patterns and generate alert messages for them.
        
        Returns:
            list: A list of alert message strings for any new events detected since the last check.
        """
        events = []
        # Start from the most recent change and go backwards until _last_event_check_time
        for i in range(len(self._state_log) - 1, -1, -1):
            # Get state i and state i-1 (previous entry)
            state_i = self._state_log[i]
            from datetime import datetime
            t_i = datetime.strptime(state_i[0] + " " + state_i[1], "%d-%m-%y %H:%M:%S")
            if t_i <= self._last_event_check_time:
                # Reached changes that were already checked
                break
            if i == 0:
                # No previous entry to compare (this is the first log entry)
                continue
            state_prev = self._state_log[i-1]
            # Compute difference between state_i and state_prev
            dict_i = {state_i[j]: state_i[j+1] for j in range(3, len(state_i), 2)}
            dict_prev = {state_prev[j]: state_prev[j+1] for j in range(3, len(state_prev), 2)}
            change = {k: dict_i[k] for k in dict_i if dict_i[k] != dict_prev.get(k, None)}
            # Check if this change matches any known event pattern
            change_key = frozenset(change.items())
            if change_key in DummyBlueforsSlave.EVENT_MARKERS:
                events.append(DummyBlueforsSlave.EVENT_MARKERS[change_key])
        # Update last_event_check_time to the latest checked change
        if self._state_log:
            latest_time_str = self._state_log[-1][0] + " " + self._state_log[-1][1]
            self._last_event_check_time = datetime.strptime(latest_time_str, "%d-%m-%y %H:%M:%S")
        return events
    
    def generate_state_message(self):
        """
        Generate a formatted message string summarizing the current state of the system.
        
        The message includes the status of main components (with symbols indicating on/off), 
        key temperature readings, and other relevant information.
        
        Returns:
            str: A multi-line string message representing the current state.
        """
        # Symbols for state: using a white circle for off (0), green circle for on (1), and yellow circle for transitional (2).
        on_off_symbol = {"0": "⚪️", "1": "🟢", "2": "🟡"}
        last_state = self.dict_state(0)  # get current state as dict
        status_entry = self.get_status()
        status_dict = {}
        if status_entry:
            # Convert status_entry (list) to dict of sensor readings
            for j in range(2, len(status_entry), 2):
                key = status_entry[j]
                val = status_entry[j+1]
                status_dict[key] = val
        # Determine compressor sensor variant for water temperatures (if applicable)
        variant = -1
        if "cptempwo" in status_dict:
            variant = 0
        elif "cpatempwo" in status_dict:
            variant = 1
        # Prepare main components status line
        main_components = ["scroll1", "scroll2", "turbo1", "compressor", "pulsetube"]
        main_labels = ["scr1", "scr2", "tur1", "comp", "pt  "]
        main_status_parts = []
        for key, label in zip(main_components, main_labels):
            state_val = last_state.get(key, "0")
            # If turbo is on but not at speed (transitional), or vice versa, mark as transitional
            if key == "turbo1":
                turbo_on = (state_val == "1")
                turbo_speed = False
                if "tc400setspdatt" in status_dict:
                    try:
                        turbo_speed = (float(status_dict["tc400setspdatt"]) == 1.0)
                    except:
                        turbo_speed = (str(status_dict["tc400setspdatt"]) == "1")
                if turbo_on ^ turbo_speed:
                    # Mark turbo as transitional
                    state_val = "2"
            if key == "pulsetube":
                # Check pulsetube transitional state: if compressor or pulsetube not fully synchronized (simple heuristic)
                comp_on = (last_state.get("compressor", "0") == "1")
                pt_on = (state_val == "1")
                if pt_on and not comp_on:
                    state_val = "2"  # pulsetube on but compressor off -> not a valid state, mark as transitional/fault
            symbol = on_off_symbol.get(state_val, "⚪️")
            main_status_parts.append(f"{symbol}{label}")
        main_status_line = " ".join(main_status_parts)
        # Prepare temperature readings line
        temp_parts = []
        temp_parts.append(f"MC: {float(status_dict.get('mix_chamber', self.sensors['mix_chamber'])):.2f} K")
        temp_parts.append(f"Still: {float(status_dict.get('still', self.sensors['still'])):.2f} K")
        temp_parts.append(f"Plate: {float(status_dict.get('platform', self.sensors['platform'])):.2f} K")
        temps_line = " | ".join(temp_parts)
        # Prepare compressor water temperature line (if available)
        water_line = ""
        if variant != -1:
            wo_key = "cptempwo" if variant == 0 else "cpatempwo"
            wi_key = "cptempwi" if variant == 0 else "cpatempwi"
            try:
                wo_val = float(status_dict.get(wo_key, 0.0))
                wi_val = float(status_dict.get(wi_key, 0.0))
            except:
                wo_val = float(self.sensors.get(wo_key, 0.0))
                wi_val = float(self.sensors.get(wi_key, 0.0))
            water_line = f"Water In/Out: {wi_val:.1f} °C / {wo_val:.1f} °C"
        # Prepare vacuum pressures line (show one or two critical pressures)
        pressures = self.get_last_pressures()
        pressure_line = ""
        if pressures:
            # For example, display the lowest pressure (highest vacuum)
            lowest_p = min(pressures)
            pressure_line = f"Lowest vacuum: {DummyBlueforsSlave.format_unicode_sci(lowest_p)} mbar"
        # Combine all parts into a multi-line message
        message_lines = [
            f"**System Status**: {main_status_line}",
            f"**Temperatures**: {temps_line}"
        ]
        if water_line:
            message_lines.append(f"**Compressor Water**: {water_line}")
        if pressure_line:
            message_lines.append(f"**Vacuum**: {pressure_line}")
        return "\n".join(message_lines)
    
    @staticmethod
    def format_unicode_sci(number):
        """
        Format a number in scientific notation using Unicode superscript for the exponent (for negative exponents only).
        Returns a string like "1.23·10⁻⁴" for 1.23e-4.
        If the number is not in a range that requires scientific notation, the original number is returned as a string.
        """
        import math
        try:
            if number == 0:
                return "0"
            exponent = int(math.floor(math.log10(abs(number))))
            if exponent < -1 or exponent > 3:
                # Represent in mantissa · 10^exp form
                mantissa = number / (10 ** exponent)
                # Create translation map for superscripts
                sup_map = str.maketrans("0123456789-", "⁰¹²³⁴⁵⁶⁷⁸⁹⁻")
                return f"{mantissa:.2f}·10" + str(exponent).translate(sup_map)
            else:
                # If exponent is between -1 and 3, just return a normal float with appropriate decimals
                return f"{number:.3f}"
        except Exception:
            return str(number)
    
    def set_channel(self, channel, value):
        """
        Set the state of a given channel (component) and log the change.
        
        Parameters:
            channel (str): The name of the channel (e.g., 'pulsetube', 'compressor', 'v5', etc).
            value (int or str): The new state value for the channel (0/1/2 or '0'/'1'/'2').
        
        Returns:
            None
        """
        from datetime import datetime
        # Normalize value to string
        val_str = str(value)
        if channel not in self.state:
            raise KeyError(f"Unknown channel '{channel}'")
        if val_str not in ("0", "1", "2"):
            raise ValueError("State value must be 0, 1, or 2 (or their string equivalents).")
        # If no change, do nothing
        if self.state[channel] == val_str:
            return
        # Update the state
        self.state[channel] = val_str
        # If the channel is the pulse tube or compressor, we might update certain sensors accordingly
        if channel == 'pulsetube':
            if val_str == "1":
                # Pulsetube turned on -> system will start cooling (immediate small drop in temps for simulation)
                self.sensors['mix_chamber'] = max(0.1, self.sensors['mix_chamber'] - 50.0)
                self.sensors['still'] = max(1.0, self.sensors['still'] - 50.0)
            else:
                # Pulsetube turned off -> system will warm up (immediate rise in temps for simulation)
                self.sensors['mix_chamber'] = min(300.0, self.sensors['mix_chamber'] + 10.0)
                self.sensors['still'] = min(300.0, self.sensors['still'] + 10.0)
        if channel == 'compressor':
            if val_str == "0":
                # Compressor off -> water temperatures drift toward ambient
                self.sensors['cptempwi'] = min(25.0, self.sensors['cptempwi'] + 1.0)
                self.sensors['cptempwo'] = min(25.0, self.sensors['cptempwo'] + 1.0)
            else:
                # Compressor on -> water temperatures drop slightly (pump cooling water flow)
                self.sensors['cptempwi'] = max(15.0, self.sensors['cptempwi'] - 1.0)
                self.sensors['cptempwo'] = max(15.0, self.sensors['cptempwo'] - 1.0)
        if channel == 'turbo1':
            if val_str == "1":
                # Turbo turned on -> mark turbo speed not yet attained
                self.sensors['tc400setspdatt'] = 0
            else:
                # Turbo off -> reset speed attained sensor
                self.sensors['tc400setspdatt'] = 0
        # Log the new state and update status and pressures at this timestamp
        now = datetime.now()
        self._log_state(now)
        self._log_status(now)
        # Adjust pressure readings if vacuum pumps/turbo were toggled (simulated effect on vacuum)
        if channel in ['scroll1', 'scroll2', 'turbo1']:
            if val_str == "1":
                # Pump turned on -> vacuum improves (pressure drops by factor 10)
                self.pressures = [p/10 if p > 0 else p for p in self.pressures]
            else:
                # Pump turned off -> vacuum worsens (pressure rises by factor 10)
                self.pressures = [p*10 for p in self.pressures]
        self._log_pressures(now)
    
    def toggle_pulsetube(self):
        """Toggle the pulse tube on/off (if currently '0' -> set to '1', if '1' or '2' -> set to '0')."""
        current = self.state.get('pulsetube', '0')
        new = '1' if current == '0' else '0'
        self.set_channel('pulsetube', new)
    
    def toggle_compressor(self):
        """Toggle the helium compressor on/off."""
        current = self.state.get('compressor', '0')
        new = '1' if current == '0' else '0'
        self.set_channel('compressor', new)
    
    def toggle_turbo(self):
        """Toggle the turbo pump on/off."""
        current = self.state.get('turbo1', '0')
        new = '1' if current == '0' else '0'
        self.set_channel('turbo1', new)
    
    def toggle_valve(self, valve_name):
        """
        Toggle a valve state (open/closed).
        
        Parameters:
            valve_name (str): The name of the valve (e.g., 'v5', 'v6', etc).
        """
        if valve_name not in self.state or not valve_name.startswith('v'):
            raise KeyError(f"Unknown valve '{valve_name}'")
        current = self.state[valve_name]
        new = '1' if current == '0' else '0'
        self.set_channel(valve_name, new)
    
    def toggle_heat_switch(self, hs_name):
        """
        Toggle a heat switch (e.g., 'hs-still' or 'hs-mc').
        
        Parameters:
            hs_name (str): Heat switch name ('hs-still' or 'hs-mc').
        """
        if hs_name not in self.state or not hs_name.startswith('hs'):
            raise KeyError(f"Unknown heat switch '{hs_name}'")
        current = self.state[hs_name]
        new = '1' if current == '0' else '0'
        self.set_channel(hs_name, new)

if __name__ == "__main__":
    dummy = DummyBlueforsSlave("nickname", "password", "localhost", 1234)
    dummy.toggle_pulsetube()                     # simulate turning the pulse tube on
    print(dummy.generate_state_message())        # get a status report string
    print(dummy.generate_alert_messages())       # check for any alert events triggered
    last_change = dummy.get_last_state_change()  # get the most recent state change details
    print("Last change:", last_change)
