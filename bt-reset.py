import time
import subprocess
import logging
from datetime import datetime, timedelta
from pwnagotchi.plugins import Plugin

class BTReset(Plugin):
    __author__ = 'NeonLightning'
    __version__ = '1.0.0'
    __license__ = 'GPL3'
    __description__ = 'Restarts Pwnagotchi if Bluetooth is not connected for long enough.'

    def on_loaded(self):
        logging.info("[BT-Reset] Loading")

    def on_unload(self, *args):
        self.selfrunning = False
        logging.info("[BT-Reset] plugin unloaded.")

    def on_ui_update(self, ui):
        tether_status = ui.get("bluetooth")
        if tether_status is not None:
            ui.set("bluetooth", tether_status + " *")
        if self.remaining_timeout is not None:
            remaining_seconds = int(self.remaining_timeout)
            logging.debug(f"Remaining seconds: {remaining_seconds}")
            ui.set("bluetooth", tether_status + " * " + str(remaining_seconds) + "s")

    def check_bluetooth_status(self):
        result = subprocess.run(['bluetoothctl', 'info'], capture_output=True, text=True)
        if 'Connected: yes' in result.stdout:
            self.last_connected = datetime.now()
            if not self.was_connected:
                logging.info("[BT-Reset] Bluetooth is connected. Updating last connected time.")
                self.was_connected = True
        else:
            logging.debug("[BT-Reset] Bluetooth is not connected")
            time_disconnected = datetime.now() - self.last_connected
            logging.debug(f"[BT-Reset] Bluetooth time disconnected. {time_disconnected}")
            self.remaining_timeout = self.timeout_minutes * 60 - time_disconnected.total_seconds()
            logging.info(f"[BT-Reset] No active Bluetooth connections detected. Disconnected for {time_disconnected}. Restarting Pwnagotchi service in {self.remaining_timeout} seconds.")
            if self.was_connected:
                logging.info("[BT-Reset] Bluetooth has been disconnected.")
                self.was_connected = False
            if self.remaining_timeout <= 0:
                logging.info(f"[BT-Reset] Bluetooth not connected for {self.timeout_minutes} minutes. Restarting Pwnagotchi service.")
                subprocess.run(['sudo', 'systemctl', 'restart', 'pwnagotchi'], check=True)

    def on_ready(self, agent):
        self.timeout_minutes = self.options.get('timeout_minutes', 30)
        self.last_connected = datetime.now()
        self.was_connected = False
        self.selfrunning = True
        logging.info(f"[BT-Reset] plugin loaded with timeout of {self.timeout_minutes} minutes.")
        while self.selfrunning:
            self.check_bluetooth_status()
            time.sleep(10)