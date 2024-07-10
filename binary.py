from pwnagotchi.ui.components import LabeledValue
from pwnagotchi.ui.view import BLACK
import pwnagotchi.ui.fonts as fonts
import pwnagotchi.plugins as plugins
import pwnagotchi
import logging
from datetime import datetime

class BinClock(plugins.Plugin):
    __author__ = 'NeonLightning'
    __version__ = '1.0.0'
    __license__ = 'GPL3'
    __description__ = 'Clock/Calendar for pwnagotchi'

    def on_loaded(self):
        self.format = self.options.get('format', "%H:%M")
        logging.info("[BinClock] Loaded")

    def on_ui_setup(self, ui):
        pos = (10, 10)
        ui.add_element('binclock', LabeledValue(color=BLACK, label='', value='-:-',
                                                position=pos,
                                                label_font=fonts.Small, text_font=fonts.Small))
        
    def on_ui_update(self, ui):
        now = datetime.now()
        current_time = now.strftime(self.format)
        binary_time = "\n".join(format(int(part), '06b') for part in current_time.split(":"))
        ui.set('binclock', binary_time)

    def on_unload(self, ui):
        with ui._lock:
            ui.remove_element('binclock')
        logging.info("[BinClock] unloaded")