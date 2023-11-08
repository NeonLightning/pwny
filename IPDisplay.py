#main.plugins.IPDisplay.enabled = true
#main.plugins.IPDisplay.enable_eth0 = true
#main.plugins.IPDisplay.enable_usb0 = true
#main.plugins.IPDisplay.enable_bnep0 = true
#main.plugins.IPDisplay.enable_wlan0 = true

from pwnagotchi.ui.components import LabeledValue
from pwnagotchi.ui.view import BLACK
import pwnagotchi.ui.fonts as fonts
import pwnagotchi.plugins as plugins
import pwnagotchi
import logging
import subprocess

class IPDisplay(plugins.Plugin):
    __author__ = 'NeonLightning'
    __version__ = '0.9.1'
    __license__ = 'GPL3'
    __description__ = 'Display IP addresses on the Pwnagotchi UI'

    def on_loaded(self):
        self.config = self.options
        logging.info("IP Display Plugin loaded.")

    def on_ui_setup(self, ui):
        if self.config.get('enable_eth0', False):
            pos1 = (150, 11)
            ui.add_element('ip1', LabeledValue(color=BLACK, label='ETH0:', value='Disconnected',
                                              position=pos1, label_font=fonts.Small, text_font=fonts.Small))
        if self.config.get('enable_usb0', False):
            pos2 = (150, 21)
            ui.add_element('ip2', LabeledValue(color=BLACK, label='USB0:', value='Disconnected',
                                              position=pos2, label_font=fonts.Small, text_font=fonts.Small))
        if self.config.get('enable_bnep0', False):
            pos3 = (150, 31)
            ui.add_element('ip3', LabeledValue(color=BLACK, label='BT0 :', value='Disconnected',
                                              position=pos3, label_font=fonts.Small, text_font=fonts.Small))
        if self.config.get('enable_wlan0', False):
            pos3 = (150, 41)
            ui.add_element('ip4', LabeledValue(color=BLACK, label='WLAN:', value='Disconnected',
                                              position=pos3, label_font=fonts.Small, text_font=fonts.Small))

    def on_ui_update(self, ui):
        eth0_enabled = self.config.get('enable_eth0', False)
        usb0_enabled = self.config.get('enable_usb0', False)
        bnep0_enabled = self.config.get('enable_bnep0', False)
        wlan0_enabled = self.config.get('enable_wlan0', False)
        eth0_ip = subprocess.getoutput("ip -4 addr show eth0 | grep -oP '(?<=inet\s)\d+(\.\d+){3}' | head -1")
        usb0_ip = subprocess.getoutput("ip -4 addr show usb0 | grep -oP '(?<=inet\s)\d+(\.\d+){3}' | head -1")
        bnep0_ip = subprocess.getoutput("ip -4 addr show bnep0 | grep -oP '(?<=inet\s)\d+(\.\d+){3}' | head -1")
        wlan0_ip = subprocess.getoutput("ip -4 addr show wlan0 | grep -oP '(?<=inet\s)\d+(\.\d+){3}' | head -1")
        eth0_ip = eth0_ip if eth0_enabled and "Device \"eth0\" does not exist." not in eth0_ip and eth0_ip.strip() != '' else 'Disconnected'
        usb0_ip = usb0_ip if usb0_enabled and "Device \"usb0\" does not exist." not in usb0_ip and usb0_ip.strip() != '' else 'Disconnected'
        bnep0_ip = bnep0_ip if bnep0_enabled and "Device \"bnep0\" does not exist." not in bnep0_ip and bnep0_ip.strip() != '' else 'Disconnected'
        wlan0_ip = wlan0_ip if wlan0_enabled and "Device \"wlan0\" does not exist." not in wlan0_ip and wlan0_ip.strip() != '' else 'Disconnected'
        if eth0_enabled:
            if eth0_ip != 'Disconnected':
                ui.set('ip1', eth0_ip)
        if usb0_enabled:
            if usb0_ip != 'Disconnected':
                ui.set('ip2', usb0_ip)
        if bnep0_enabled:
            if bnep0_ip != 'Disconnected':
                ui.set('ip3', bnep0_ip)
        if wlan0_enabled:
            if wlan0_ip != 'Disconnected':
                ui.set('ip4', wlan0_ip)

    def on_unload(self, ui):
        with ui._lock:
            if self.config.get('enable_eth0', True):
                ui.remove_element('ip1')
            if self.config.get('enable_usb0', True):
                ui.remove_element('ip2')
            if self.config.get('enable_bnep0', True):
                ui.remove_element('ip3')
            if self.config.get('enable_wlan0', True):
                ui.remove_element('ip4')