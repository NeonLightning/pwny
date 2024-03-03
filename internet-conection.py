#internet-conection.png and internet-conection-off.png required
# still have to manually setup positions either in this file or using tweak_view

import logging, os, pwnagotchi, urllib.request, requests
import pwnagotchi.ui.components as components
import pwnagotchi.ui.view as view
import pwnagotchi.ui.fonts as fonts
import pwnagotchi.plugins as plugins
from pwnagotchi.ui.components import Text
from pwnagotchi import plugins
from PIL import ImageOps, Image

class InetIcon(pwnagotchi.ui.components.Widget):
    def __init__(self, value="", position=(220, 101), color=0, png=False):
        super().__init__(position, color)
        self.value = value

    def draw(self, canvas, drawer):
        if self.value is not None:
            self.image = Image.open(self.value)
            self.image = self.image.convert('RGBA')
            self.pixels = self.image.load()
            for y in range(self.image.size[1]):
                for x in range(self.image.size[0]):
                    if self.pixels[x,y][3] < 255:    # check alpha
                        self.pixels[x,y] = (255, 255, 255, 255)
            if self.color == 255:
                self._image = ImageOps.colorize(self.image.convert('L'), black = "white", white = "black")
            else:
                self._image = self.image
            self.image = self._image.convert('1')
            canvas.paste(self.image, self.xy)   

class InternetConnectionPlugin(plugins.Plugin):
    __author__ = 'neonlightning'
    __version__ = '1.0.2'
    __license__ = 'GPL3'
    __description__ = 'A plugin that displays the Internet connection status on the pwnagotchi display.'
    __name__ = 'InternetConectionPlugin'
    __help__ = """
    A plugin that displays the Internet connection status on the pwnagotchi display.
    """

    __defaults__ = {
        'enabled': False,
    }
    def __init__(self):
        self.icon_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "internet-conection.png")
        self.icon_off_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "internet-conection-off.png")

    def download_icon(self, url, save_path):
        response = requests.get(url)
        with open(save_path, 'wb') as file:
            file.write(response.content)

    def on_loaded(self):
        if not os.path.exists(self.icon_path):
            logging.info("internet-conection: on icon path not found")
            self.download_icon("https://raw.githubusercontent.com/NeonLightning/pwny/main/internet-conection.png", self.icon_path)
        if not os.path.exists(self.icon_off_path):
            logging.info("internet-conection: off icon path not found")
            self.download_icon("https://raw.githubusercontent.com/NeonLightning/pwny/main/internet-conection-off.png", self.icon_off_path)
        logging.info("Internet Connection Plugin loaded.")
        
    def on_ui_setup(self, ui):
        try:
            ui.add_element('connection_status', InetIcon(value=self.icon_path, png=True)) 
        except Exception as e:
            logging.info(f"Error loading {e}")
                         
        ui.add_element('ineticon', components.LabeledValue(color=view.BLACK, label='Inet:', value='',
                                                                   position=(195, 100), label_font=fonts.Small, text_font=fonts.Small))
        if self._is_internet_available():
            ui.set('connection_status', self.icon_path) 
        else:
            ui.set('connection_status', self.icon_off_path)

    def on_ui_update(self, ui):
        if self._is_internet_available():
            ui.set('connection_status', self.icon_path) 
        else:
            ui.set('connection_status', self.icon_off_path)

    def on_unload(self, ui):
        with ui._lock:
            try:
                ui.remove_element('ineticon')
            except KeyError:
                pass
            try:
                ui.remove_element('connection_status')
            except KeyError:
                pass
        logging.info("Internet Connection Plugin unloaded.")
            
    def _is_internet_available(self):
        try:
            urllib.request.urlopen('https://www.google.com', timeout=0.5)
            return True
        except urllib.request.URLError:
            return False