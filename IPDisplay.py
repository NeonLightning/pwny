############################
# setup is simple
# main.plugins.IPDisplay.devices = [
#     'eth0',
#     'usb0',
#     'bnep0',
#     'wlan0',
#     'ect...'
# ]

from pwnagotchi.ui.components import LabeledValue
from pwnagotchi.ui.view import BLACK
import pwnagotchi.ui.fonts as fonts
import pwnagotchi.plugins as plugins
from pwnagotchi import config
import pwnagotchi
import logging
import subprocess
import time

class IPDisplay(plugins.Plugin):
    __author__ = 'NeonLightning'
    __version__ = '0.9.5'
    __license__ = 'GPL3'
    __description__ = 'Display IP addresses on the Pwnagotchi UI'

    def on_loaded(self):
        self.device_list = config['main']['plugins']['IPDisplay'].get('devices', [])
        if self.device_list == None:
            self.device_list = [bnep0]
        self.device_index = 0
        self.ui_element_name = 'ip1'
        self.ready = False  # Initialize ready state to False
        logging.info("IP Display Plugin loaded.")

    def on_ready(self, agent):
        self.ready = True

    def on_ui_setup(self, ui):
        pos1 = (150, 13)
        ui.add_element(self.ui_element_name, LabeledValue(color=BLACK, label="", value='Initializing...',
                                            position=pos1, label_font=fonts.Small, text_font=fonts.Small))

    def on_ui_update(self, ui):
        if not self.ready:
            return
        if not self.device_list:
            logging.debug("No devices found in the list.")
            return
        current_device = self.device_list[self.device_index]
        command = f"ip -4 addr show {current_device} | awk '/inet / {{print $2}}' | cut -d '/' -f 1 | head -n 1"
        netip = subprocess.getoutput(command)
        if netip != '':
            ui.set(self.ui_element_name, f'{current_device}:{netip}')
        else:
            logging.debug(f"No IP address found for {current_device}")
        self.device_index = (self.device_index + 1) % len(self.device_list)

    def on_unload(self, ui):
        self.ready = False
        ui.remove_element(self.ui_element_name)
        logging.info("IP Display Plugin unloaded.")
