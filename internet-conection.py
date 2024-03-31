#internet-conection.png and internet-conection-off.png required (Auto Downloads If internet If Provided)
import socket
import logging, os, pwnagotchi, requests
import pwnagotchi.ui.components as components
import pwnagotchi.ui.view as view
import pwnagotchi.ui.fonts as fonts
import pwnagotchi.plugins as plugins
from pwnagotchi.ui.components import Text
from pwnagotchi import plugins
from PIL import ImageOps, Image

class InetIcon(pwnagotchi.ui.components.Widget):
    def __init__(self, value="", position=(235, 101), color=0, png=False):
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
    __version__ = '1.0.3'
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
        self.icon_invert_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "internet-conection-invert.png")
        self.icon_invert_off_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "internet-conection-off-invert.png")

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

        if not os.path.exists(self.icon_invert_path):
            logging.info("internet-conection: on icon path not found")
            self.download_icon("https://raw.githubusercontent.com/NeonLightning/pwny/main/internet-conection-invert.png", self.icon_invert_path)

        if not os.path.exists(self.icon_invert_off_path):
            logging.info("internet-conection: off icon path not found")
            self.download_icon("https://raw.githubusercontent.com/NeonLightning/pwny/main/internet-conection-off-invert.png", self.icon_invert_off_path)

    def on_ui_setup(self, ui):
        global invert_status
        try:
            ui.add_element('connection_status', InetIcon(value=self.icon_path, png=True)) 
        except Exception as e:
            logging.info(f"Error loading {e}")
        ui.add_element('ineticon', components.LabeledValue(color=view.BLACK, label='', value='',
                                                                   position=(235, 100), label_font=fonts.Small, text_font=fonts.Small))
        invert_status = self.invert()
        if invert_status == False:

            if self._is_internet_available():
                ui.set('connection_status', self.icon_path) 
            else:
                ui.set('connection_status', self.icon_off_path)
        elif invert_status == True:
            if self._is_internet_available():
                ui.set('connection_status', self.icon_invert_path) 
            else:
                ui.set('connection_status', self.icon_invert_off_path)
    def on_ui_update(self, ui):
        if invert_status == False:

            if self._is_internet_available():
                ui.set('connection_status', self.icon_path) 
            else:
                ui.set('connection_status', self.icon_off_path)            
        elif invert_status == True:
            if self._is_internet_available():
                ui.set('connection_status', self.icon_invert_path) 
            else:
                ui.set('connection_status', self.icon_invert_off_path)
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
            socket.create_connection(("www.google.com", 80))
            return True
        except OSError:
            return False
        
    def invert(self):
        try:
            with open("/etc/pwnagotchi/config.toml", "r") as f:
                config = f.readlines()
        except FileNotFoundError:
            logging.warning("Internet-Connection: Config File not found")
            return False
        except EOFError:
            pass
        
        for line in config:
            line = line.strip()
            line = line.strip('\n')
            if "ui.invert = true" in line or "ui.invert = false" in line or "ui.invert = True" in line or "ui.invert = False" in line or "ui.invert=TRUE" in line or "ui.invert=FALSE" in line:

                if line.find("ui.invert = true") != -1:
                    logging.info("Internet-Connection: Screen Invert True")
                    return True
                    
                elif line.find("ui.invert = false") != -1:
                    logging.info("Internet-Connection: Screen Invert False")
                    return False
        
        logging.info("Internet-Connection: Screen Invert Error")
        return False
