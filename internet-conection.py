import logging, time
import pwnagotchi.ui.components as components
import pwnagotchi.ui.view as view
import pwnagotchi.ui.fonts as fonts
import pwnagotchi.plugins as plugins
import pwnagotchi
import subprocess

class InternetConnectionPlugin(plugins.Plugin):
    __author__ = 'adi1708 made by chatGPT'
    __version__ = '1.0.0'
    __license__ = 'GPL3'
    __description__ = 'A plugin that displays the Internet connection status on the pwnagotchi display.'
    __name__ = 'InternetConnectionPlugin'
    __help__ = """
    A plugin that displays the Internet connection status on the pwnagotchi display.
    """

    __defaults__ = {
        'enabled': False,
    }

    def on_loaded(self):
        logging.info("Internet Connection Plugin loaded.")

    def on_ui_setup(self, ui):
        ui.add_element('connection_status', components.LabeledValue(color=view.BLACK, label='Internet:', value='',
                                                                   position=(0, 50), label_font=fonts.Small, text_font=fonts.Small))
        try:
            output = subprocess.check_output(['ping', '-c', '1', 'google.com'])
            ui.set('connection_status', 'Connected')
        except subprocess.CalledProcessError:
            ui.set('connection_status', 'Disconnected')

    def on_epoch(self, ui):
        try:
            output = subprocess.check_output(['ping', '-c', '1', 'google.com'])
            ui.set('connection_status', 'Connected')
        except subprocess.CalledProcessError:
            ui.set('connection_status', 'Disconnected')
