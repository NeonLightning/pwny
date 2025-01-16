import logging
import os
import time
import subprocess
import pwnagotchi.plugins as plugins
from pwnagotchi.ui.components import LabeledValue, Text
from pwnagotchi.ui.view import BLACK
import pwnagotchi.ui.fonts as fonts
import pwnagotchi.utils as utils

class ServiceUptime(plugins.Plugin):
    __author__ = 'neonlightning'
    __version__ = '1.0.2'
    __license__ = 'GPL3'
    __description__ = 'Logs and displays Pwnagotchi service uptime'

    def __init__(self):
        try:
            result = subprocess.check_output(['systemctl', 'show', '-p', 'ActiveEnterTimestamp', 'pwnagotchi.service'])
            start_time_str = ' '.join(result.decode().strip().split('=')[1].split()[1:-1])
            self._start_time = time.strptime(start_time_str, '%Y-%m-%d %H:%M:%S')
            self._start = time.mktime(self._start_time)
            start_str = time.strftime("%Y-%m-%d %H:%M:%S", self._start_time)
        except Exception as e:
            logging.error(f"[service uptime] Error getting pwnagotchi.service start time: {e}")
        log_dir = "/home/pi/uptime_log/"
        os.makedirs(log_dir, exist_ok=True)
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        self._log_file_path = os.path.join(log_dir, f"service_uptime-{timestamp}.log")
        with open(self._log_file_path, "w") as file:
            file.write(f"Service uptime log started at {self._start_time}\n")
        self._last_log_time = time.time()
        self._last_ui_update_time = time.time()
        self._first_run = True
        logging.info(f"[service uptime] service started at {start_str}")

    def _log_uptime(self, message):
        with open(self._log_file_path, "w") as file:
            file.write(message)

    def on_unload(self, ui):
        with ui._lock:
            try:
                ui.remove_element('service_uptime')
            except Exception as e:
                logging.error(f"[service uptime] Error during UI cleanup: {e}")
        logging.info(f"[service uptime] Plugin unloaded")

    def on_ui_setup(self, ui):
        try:
            pos = self.options.get('position', f"{ui.width() - 90},12").split(',')
            pos = [int(x.strip()) for x in pos]
            ui.add_element('service_uptime', LabeledValue(color=BLACK, label="Srv: ", value="-:-:-", position=pos, label_font=fonts.Small, text_font=fonts.Small))
        except Exception as err:
            logging.warning(f"[service uptime] UI setup error: {repr(err)}")

    def on_ui_update(self, ui):
        current_time = time.time()
        elapsed_time = current_time - self._start
        uptime_str = utils.secs_to_hhmmss(elapsed_time)
        if self._first_run:
            ui.set('service_uptime', f"Srv: {uptime_str}")
            self._first_run = False
        if current_time - self._last_log_time >= 5:
            self._log_uptime(f"Service uptime log started at {time.strftime('%Y-%m-%d %H:%M:%S', self._start_time)} Uptime: {uptime_str}\n")
            self._last_log_time = current_time
        if current_time - self._last_ui_update_time >= 10:
            ui.set('service_uptime', uptime_str)
            self._last_ui_update_time = current_time