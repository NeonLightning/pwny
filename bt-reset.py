# you can configure the time using
# main.plugins.btreset.timeout_minutes = 30
import time, subprocess, logging
from datetime import datetime, timedelta
from pwnagotchi.plugins import Plugin

class BTReset(Plugin):
    __author__ = 'NeonLightning'
    __version__ = '1.0.0'
    __license__ = 'GPL3'
    __description__ = 'Restarts Pwnagotchi if Bluetooth is not connected for long enough.'

    def __init__(self):
        self.last_connected = datetime.now()
        self.timeout_minutes = 30

    def on_loaded(self):
        self.selfrunning = True
        self.timeout_minutes = self.options.get('timeout_minutes', 30)
        logging.info(f"[BT-Reset] plugin loaded with timeout of {self.timeout_minutes} minutes.")

    def on_unload(self, *args):
        self.selfrunning = False
        logging.info("[BT-Reset] plugin unloaded.")

    def check_bluetooth_status(self):
        result = subprocess.run(['hcitool', 'con'], capture_output=True, text=True)
        if 'Connections:' in result.stdout and 'ACL' in result.stdout:
            self.last_connected = datetime.now()
        else:
            if datetime.now() - self.last_connected > timedelta(minutes=self.timeout_minutes):
                logging.info(f"[BT-Reset] Bluetooth not connected for {self.timeout_minutes} minutes. Restarting Pwnagotchi service.")
                subprocess.run(['sudo', 'pwnkill'])

    def on_ready(self, agent):
        while self.selfrunning:
            self.check_bluetooth_status()
            time.sleep(60)
