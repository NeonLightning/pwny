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
import logging
import subprocess
import ipaddress


class IPDisplay(plugins.Plugin):
    __author__ = 'NeonLightning'
    __version__ = '0.9.5'
    __license__ = 'GPL3'
    __description__ = 'Display IP addresses on the Pwnagotchi UI'

    def __init__(self):
        self.options = dict()
        self.device_list = []
        self.device_index = 0
        self.ready = False

    def on_loaded(self):
        self.device_list = self.options['devices']
        if self.device_list is None:
            self.device_list = ['bnep0']
        self.device_index = 0
        logging.debug("IP Display Plugin loaded.")
        
    def on_ready(self):
        self.ready = True
        logging.debug("IP Display Plugin ready.")

    def on_ui_setup(self, ui):
        pos1 = (150, 13)
        ui.add_element('ip1', LabeledValue(color=BLACK, label="", value='Initializing...',
                                           position=pos1, label_font=fonts.Small, text_font=fonts.Small))

    def on_ui_update(self, ui):
        current_device = self.device_list[self.device_index]
        logging.debug(f'IPDisplay Device {current_device}')
        command = f"ip -4 addr show {current_device} | awk '/inet / {{print $2}}' | cut -d '/' -f 1 | head -n 1"
        netip = subprocess.getoutput(command).strip()
        logging.debug(f'IPDisplay IP {netip}')
        if netip:
            try:
                ipaddress.ip_address(netip)
                ui.set('ip1', f'{current_device}:{netip}')
            except ValueError:
                logging.debug(f"Invalid IP address found for {current_device}: {netip}")
        else:
            logging.debug(f"No IP address found for {current_device}")
        self.device_index = (self.device_index + 1) % len(self.device_list)

    def on_unload(self, ui):
        self.ready = False
        ui.remove_element('ip1')
        logging.debug("IP Display Plugin unloaded.")
