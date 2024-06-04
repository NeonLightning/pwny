import logging, os, pwnagotchi, requests, socket
import pwnagotchi.ui.components as components
import pwnagotchi.ui.view as view
import pwnagotchi.ui.fonts as fonts
import pwnagotchi.plugins as plugins
from pwnagotchi.ui.components import Text
from pwnagotchi import plugins
from PIL import ImageOps, Image

class InetIcon(pwnagotchi.ui.components.Widget):
    def __init__(self, xy=(225, 101), value="", invert=False):
        super().__init__(xy=xy, color=0)
        self.value = value
        self.invert = invert

    def draw(self, canvas, drawer):
        self.image = Image.open(self.value)
        self.image = self.image.convert('RGBA')
        if self.invert:
            r, g, b, a = self.image.split()
            rgb_image = Image.merge('RGB', (r, g, b))
            inverted_rgb_image = ImageOps.invert(rgb_image)
            inverted_r, inverted_g, inverted_b = inverted_rgb_image.split()
            self.image = Image.merge('RGBA', (inverted_r, inverted_g, inverted_b, a))
        canvas.paste(self.image, self.xy)

class InternetConectionPlugin(plugins.Plugin):
    __author__ = 'neonlightning'
    __version__ = '1.0.4'
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

    def _is_internet_available(self):
        try:
            socket.create_connection(("www.google.com", 80), timeout=0.5)
            return True
        except OSError:
            return False
        
    def invert(self):
        try:
            with open("/etc/pwnagotchi/config.toml", "r") as f:
                config = f.readlines()
        except FileNotFoundError:
            logging.warning("[Internet Conection] Config File not found")
            return False
        except EOFError:
            pass
        for line in config:
            line = line.strip()
            line = line.strip('\n')
            if "ui.invert = true" in line or "ui.invert = false" in line or "ui.invert = True" in line or "ui.invert = False" in line or "ui.invert=TRUE" in line or "ui.invert=FALSE" in line:
                if line.find("ui.invert = true") != -1:
                    logging.debug("[Internet Conection] Screen Invert True")
                    return True
                elif line.find("ui.invert = false") != -1:
                    logging.debug("[Internet Conection] Screen Invert False")
                    return False
        return False
    
    def on_loaded(self):
        if not os.path.exists(self.icon_path):
            logging.info("[Internet Conection] on icon path not found")
            self.download_icon("https://raw.githubusercontent.com/NeonLightning/pwny/main/internet-conection.png", self.icon_path)
        if not os.path.exists(self.icon_off_path):
            logging.info("[Internet Conection] off icon path not found")
            self.download_icon("https://raw.githubusercontent.com/NeonLightning/pwny/main/internet-conection-off.png", self.icon_off_path)
        logging.info("[Internet Conection] Plugin loaded.")

    def on_ui_setup(self, ui):
        invert_status = self.invert()
        if self._is_internet_available():
            try:
                ui.add_element('connection_status', InetIcon(xy=(225, 101), value=self.icon_path, invert=invert_status))
            except Exception as e:
                logging.info(f"Error loading {e}")
        else:
            try:
                ui.add_element('connection_status', InetIcon(xy=(225, 101), value=self.icon_off_path, invert=invert_status))
            except Exception as e:
                logging.info(f"Error loading {e}")
        ui.add_element('ineticon', components.LabeledValue(color=view.BLACK, label='', value='',
                                                                   position=(195, 100), label_font=fonts.Small, text_font=fonts.Small))

    def on_ui_update(self, ui):
        invert_status = self.invert()
        if self._is_internet_available():
            ui.set('connection_status', self.icon_path, invert=invert_status)
        else:
            ui.set('connection_status', self.icon_off_path, invert=invert_status)

    def on_unload(self, ui):
        with ui._lock:
            try:
                ui.remove_element('connection_status')
            except KeyError:
                pass
            try:
                ui.remove_element('ineticon')
            except KeyError:
                pass
        logging.info("[Internet Conection] Plugin unloaded.")