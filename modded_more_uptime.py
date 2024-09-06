import logging
import os, time

import pwnagotchi.plugins as plugins
from pwnagotchi.ui.components import LabeledValue, Text
from pwnagotchi.ui.view import BLACK
import pwnagotchi.ui.fonts as fonts
import pwnagotchi.utils as utils


class Modded_More_Uptime(plugins.Plugin):
    __author__ = 'nursejackass edited by neonlightning'
    __version__ = '1.0.2'
    __license__ = 'GPL3'
    __description__ = 'Logs and displays system uptime'

    def __init__(self):
        self._agent = None
        self._start = time.time()

    # called when the plugin is loaded
    def on_loaded(self):
        self._start = time.time()

    # called before the plugin is unloaded
    def on_unload(self, ui):
        try:
            if ui.has_element('more_uptime'):
                ui.remove_element('more_uptime')
            uptimes = open('/proc/uptime').read().split()
            now = time.time()
            with open("/var/log/pwnagotchi_uptime.log", "a") as file:
                file.write("%s %s %s %s unload\n" % (now, now - self._start, uptimes[0], uptimes[1]))
        except Exception as err:
            logging.warn("[more uptime] unload this: %s" % repr(err))

    # called when the agent is rebooting the board
    def on_rebooting(self, agent):
        try:
            uptimes = open('/proc/uptime').read().split()
            now = time.time()
            with open("/var/log/pwnagotchi_uptime.log", "a") as file:
                file.write("%s %s %s %s reboot\n" % (now, now - self._start, uptimes[0], uptimes[1]))
        except Exception as err:
            logging.warn("[more uptime] reboot this: %s" % repr(err))

    # called when everything is ready and the main loop is about to start
    def on_ready(self, agent):
        self._agent = agent

    # called to setup the ui elements
    def on_ui_setup(self, ui):
        try:
            # add custom UI elements
            if not "override" in self.options or not self.options['override']:
                if "position" in self.options:
                    pos = self.options['position'].split(',')
                    pos = [int(x.strip()) for x in pos]
                else:
                    pos = (ui.width()-58, 12)

                    ui.add_element('more_uptime', Text(color=BLACK, value='up --:--', position=pos, font=fonts.Small))
        except Exception as err:
            logging.warn("[more uptime] ui setup: %s" % repr(err))

    HZ = os.sysconf(os.sysconf_names['SC_CLK_TCK'])

    def on_ui_update(self, ui):
        # update those elements
        try:
            uptimes = open('/proc/uptime').read().split()
            # get time since pwnagotchi process started
            process_stats = open('/proc/self/stat').read().split()
            res = utils.secs_to_hhmmss(float(uptimes[0]) - (int(process_stats[21])/self.HZ))
            label = "PR"
            ui.set('more_uptime', "PR %s" % (res))
            logging.debug("[more uptime] %s: %s" % (label, res))
        except Exception as err:
            logging.warn("[more uptime] ui update: %s, %s" % (repr(err), repr(uiItems)))

    def on_unload(self, ui):
        with ui._lock:
            try:
                ui.remove_element('more_uptime')
            except Exception as e:
                logging.error(f"[more uptime] {e}")