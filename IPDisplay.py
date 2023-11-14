from pwnagotchi.ui.components import LabeledValue
from pwnagotchi.ui.view import BLACK
import pwnagotchi.ui.fonts as fonts
import pwnagotchi.plugins as plugins
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
        logging.info("IP Display Plugin loaded.")
    
    def on_ready(self, agent):
        self.ready = True

    def on_ui_setup(self, ui):
        self.rotate = 0
        pos1 = (150, 13)
        ui.add_element('ip1', LabeledValue(color=BLACK, label="", value='Disconnected',
                                            position=pos1, label_font=fonts.Small, text_font=fonts.Small))

    def on_ui_update(self, ui):
        if self.ready:
            self.rotate += 1
            if self.rotate == 1:
                eth0_ip = subprocess.getoutput("ip -4 addr show eth0 | grep -oP '(?<=inet\s)\d+(\.\d+){3}' | head -1")
                eth0_ip = eth0_ip if "Device \"eth0\" does not exist." not in eth0_ip and eth0_ip.strip() != '' else 'Disconnected'
                if eth0_ip != 'Disconnected':
                    ui.set('ip1', f'Eth0:{eth0_ip}')
                    time.sleep(0.5)
                else:
                    self.rotate += 1
            if self.rotate == 2:
                usb0_ip = subprocess.getoutput("ip -4 addr show usb0 | grep -oP '(?<=inet\s)\d+(\.\d+){3}' | head -1")
                usb0_ip = usb0_ip if "Device \"usb0\" does not exist." not in usb0_ip and usb0_ip.strip() != '' else 'Disconnected'
                if usb0_ip != 'Disconnected':
                    ui.set('ip1', f'USB0:{usb0_ip}')
                    time.sleep(0.5)
                else:
                    self.rotate += 1
            if self.rotate == 3:
                bnep0_ip = subprocess.getoutput("ip -4 addr show bnep0 | grep -oP '(?<=inet\s)\d+(\.\d+){3}' | head -1")
                bnep0_ip = bnep0_ip if "Device \"bnep0\" does not exist." not in bnep0_ip and bnep0_ip.strip() != '' else 'Disconnected'
                if bnep0_ip != 'Disconnected':
                    ui.set('ip1', f'BT0 :{bnep0_ip}')
                    time.sleep(0.5)
                else:
                    self.rotate += 1
            if self.rotate == 4:
                wlan0_ip = subprocess.getoutput("ip -4 addr show wlan0 | grep -oP '(?<=inet\s)\d+(\.\d+){3}' | head -1")
                wlan0_ip = wlan0_ip if "Device \"wlan0\" does not exist." not in wlan0_ip and wlan0_ip.strip() != '' else 'Disconnected'
                if wlan0_ip != 'Disconnected':
                    ui.set('ip1', f'WLAN:{wlan0_ip}')
                    time.sleep(0.5)
                self.rotate = 0

    def on_unload(self, ui):
        self.ready = False
        with ui._lock:
            ui.remove_element('ip1')
        logging.info("IP Display Plugin unloaded.")