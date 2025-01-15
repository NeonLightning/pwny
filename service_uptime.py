import logging
import os
import time
import pwnagotchi.plugins as plugins
from pwnagotchi.ui.components import LabeledValue, Text
from pwnagotchi.ui.view import BLACK
import pwnagotchi.ui.fonts as fonts
import pwnagotchi.utils as utils

class ModdedMoreUptime(plugins.Plugin):
    __author__ = 'neonlightning'
    __version__ = '1.0.0'
    __license__ = 'GPL3'
    __description__ = 'Logs and displays Pwnagotchi service uptime'

    def __init__(self):
        self._start = time.time()
        self._start_time = time.strftime('%Y-%m-%d %H:%M:%S')
        log_dir = "/etc/pwnagotchi/log/uptime/"
        os.makedirs(log_dir, exist_ok=True)
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        self._log_file_path = os.path.join(log_dir, f"service_uptime-{timestamp}.log")
        with open(self._log_file_path, "w") as file:
            file.write(f"Service uptime log started at {self._start_time}")
        self._last_log_time = time.time()
        self._last_ui_update_time = time.time()
        self._first_run = True
        logging.info(f"[service uptime] Plugin loaded")

    def on_unload(self, ui):
        with ui._lock:
            try:
                ui.remove_element('service_uptime')
            except Exception as e:
                logging.error(f"[service uptime] Error during UI cleanup: {e}")
        logging.info(f"[service uptime] Plugin unloaded")

    def on_ui_setup(self, ui):
        current_time = time.time()
        elapsed_time = current_time - self._start
        elapsed_time = str(utils.secs_to_hhmmss(elapsed_time))
        try:
            if "position" in self.options:
                pos = self.options['position'].split(',')
                pos = [int(x.strip()) for x in pos]
            else:
                pos = (ui.width() - 90, 12)
            ui.add_element('service_uptime', LabeledValue(color=BLACK, label="Srv: ", value=elapsed_time, position=pos, label_font=fonts.Small, text_font=fonts.Small))
        except Exception as err:
            logging.warn(f"[service uptime] UI setup error: {repr(err)}")

    def on_ui_update(self, ui):
        current_time = time.time()
        if self._first_run:
            try:
                elapsed_time = current_time - self._start
                uptime_str = utils.secs_to_hhmmss(elapsed_time)
                ui.set('service_uptime', f"Srv: {uptime_str}")
                self._first_run = False
            except Exception as err:
                logging.warn(f"[service uptime] First-run UI update error: {repr(err)}")
        if current_time - self._last_log_time >= 1:
            try:
                elapsed_time = current_time - self._start
                uptime_str = utils.secs_to_hhmmss(elapsed_time)
                with open(self._log_file_path, "w") as file:
                    file.write(f"Service uptime log started at {self._start_time} Uptime: {uptime_str}\n")
                self._last_log_time = current_time
            except Exception as err:
                logging.warn(f"[service uptime] Log update error: {repr(err)}")
        if current_time - self._last_ui_update_time >= 5:
            try:
                elapsed_time = current_time - self._start
                uptime_str = utils.secs_to_hhmmss(elapsed_time)
                ui.set('service_uptime', f"{uptime_str}")
                self._last_ui_update_time = current_time
            except Exception as err:
                logging.warn(f"[service uptime] UI update error: {repr(err)}")

        
        
