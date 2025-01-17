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
    __version__ = '1.0.8'
    __license__ = 'GPL3'
    __description__ = 'Logs and displays Pwnagotchi service uptime'

    def __init__(self):
        self._start_time = None
        self._start = None
        self._last_log_time = None
        self._first_run = True
        log_dir = "/home/pi/uptime_log/"
        os.makedirs(log_dir, exist_ok=True)
        filetimestamp = time.strftime("%Y%m%d")
        self._log_file_path = os.path.join(log_dir, f"service_uptime-{filetimestamp}.log")

    def on_ready(self, agent):
        self.logging = self.options.get('logging', True)
        self._first_run = False
        logging.info(f"[service uptime] Plugin loaded")

    def on_loaded(self):
        try:
            result = subprocess.check_output(['systemctl', 'show', '-p', 'ActiveEnterTimestamp', 'pwnagotchi.service'])
            start_time_str = ' '.join(result.decode().strip().split('=')[1].split()[1:-1])
            self._start_time = time.strptime(start_time_str, '%Y-%m-%d %H:%M:%S')
            self._start = time.mktime(self._start_time)
            start_str = time.strftime("%Y-%m-%d %H:%M:%S", self._start_time)
        except Exception as e:
            logging.error(f"[service uptime] Error getting pwnagotchi.service start time: {e}")
        with open(self._log_file_path, "a+") as file:
            file.seek(0)
            self._log_line_number = sum(1 for _ in file)
            file.write(f"Service started at {start_str}. Uptime: 0:00:00\n")

        self._last_log_time = time.time()
        self._last_ui_update_time = time.time()
        logging.info(f"[service uptime] Service started at {start_str}")

    def _log_uptime(self, uptime_str):
        try:
            if not os.path.exists(self._log_file_path):
                logging.warning(f"[service uptime] Log file {self._log_file_path} was deleted. Recreating...")
                with open(self._log_file_path, "w") as file:
                    file.write(f"Service started at {time.strftime('%Y-%m-%d %H:%M:%S', self._start_time)}. Uptime: {uptime_str}\n")
                self._log_line_number = 0
                return
            with open(self._log_file_path, "r+") as file:
                lines = file.readlines()
                if self._log_line_number is not None and self._log_line_number < len(lines):
                    lines[self._log_line_number] = f"Service started at {time.strftime('%Y-%m-%d %H:%M:%S', self._start_time)}. Uptime: {uptime_str}\n"
                    file.seek(0)
                    file.writelines(lines)
                    file.truncate()
                else:
                    logging.error(f"[service uptime] Log line number {self._log_line_number} is out of bounds.")
        except Exception as e:
            logging.error(f"[service uptime] Error updating uptime log: {e}")

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
        if self._last_log_time is None:
            self._last_log_time = current_time
        if current_time - self._last_ui_update_time >= 10:
            self._last_log_time = current_time
            self.logging = self.options.get('logging', True)
            if self.logging:
                self._log_uptime(uptime_str)
                self._last_log_time = current_time
            ui.set('service_uptime', uptime_str)
            self._last_ui_update_time = current_time