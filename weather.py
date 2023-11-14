###
# main.plugins.weather.enabled = true
# main.plugins.weather.api_key = ""
# https://home.openweathermap.org/api_keys
# main.plugins.weather.areacode = "postal/zip"
# main.plugins.weather.countrycode = "countrycode"
# main.plugins.weather.gps = "/dev/ttyACM0"
# (even if you don't have a gps set this...)
# but if you want gps for weather you'll need gps.py or gps_more.py
# REQUIRES CUSTOM-FACES-MOD

import os, logging, re, pwnagotchi, toml, json, requests, urllib.request, shutil
from pwnagotchi import plugins, config
import pwnagotchi.ui.components as components
import pwnagotchi.ui.view as view
import pwnagotchi.ui.fonts as fonts
import pwnagotchi.plugins as plugins
from pwnagotchi.ui.components import Text
from pwnagotchi.bettercap import Client
from PIL import ImageDraw

agent = Client('localhost', port=8081, username="pwnagotchi", password="pwnagotchi");    

class WeatherForecast(plugins.Plugin):
    __author__ = 'NeonLightning'
    __version__ = '1.1.0'
    __license__ = 'GPL3'
    __description__ = 'A plugin that displays the weather forecast on the pwnagotchi screen.'
    __name__ = 'WeatherForecast'

    def _is_internet_available(self):
        try:
            urllib.request.urlopen('https://www.google.com', timeout=1)
            return True
        except urllib.request.URLError:
            return False
        
    def on_loaded(self):
        self.previous_seticon = None
        self.api_key = None
        self.areacode = None
        self.country = None
        self.lat = None
        self.lon = None
        self.cords = None
        self.timer = 12
        self.plugin_dir = os.path.dirname(os.path.realpath(__file__))
        self.icon_path = os.path.join(self.plugin_dir, "weather", "display.png")
        self.icon_position_x = 147
        self.icon_position_y = 35
        self.icon = Text(value=self.icon_path, png=True, position=(self.icon_position_x, self.icon_position_y))
        self.api_key = config['main']['plugins']['weather']['api_key']
        self.areacode = config['main']['plugins']['weather']['areacode']
        self.country = config['main']['plugins']['weather']['countrycode']
        self.gps = config['main']['plugins']['weather']['gps']
        self.geo_url = f"http://api.openweathermap.org/geo/1.0/zip?zip={self.areacode},{self.country}&appid={self.api_key}"
        self._update_lat_lon()
        logging.info(f"Weather Forecast Loaded")

    def _update_lat_lon(self):
        if config['main']['plugins']['gps']['enabled'] or config['main']['plugins']['gps_more']['enabled']:
            try:
                info = agent.session()
                coords = info.get("gps", {})
                if all([coords.get("Latitude"), coords.get("Longitude")]):
                    self.lat = coords["Latitude"]
                    self.lon = coords["Longitude"]
            except Exception as err:
                logging.warn(f"Failed to get GPS coordinates: {err}")
        else:
            try:
                geo_response = requests.get(self.geo_url).json()
                self.lat = geo_response.get('lat')
                self.lon = geo_response.get('lon')
            except Exception as err:
                logging.error(f"Error fetching latitude and longitude: {err}")
        self.weather_url = f"https://api.openweathermap.org/data/2.5/weather?lat={self.lat}&lon={self.lon}&appid={self.api_key}"
        if self._is_internet_available():
            self.weather_response = requests.get(self.weather_url).json()

    def on_ui_setup(self, ui):
        ui.add_element('feels', components.LabeledValue(color=view.BLACK, label='', value='',
                                                                   position=(90, 85), label_font=fonts.Small, text_font=fonts.Small))
        ui.add_element('main', components.LabeledValue(color=view.BLACK, label='', value='',
                                                            position=(90, 100), label_font=fonts.Small, text_font=fonts.Small))
        ui.add_element('icon', self.icon)
    
    def on_epoch(self, agent, epoch, epoch_data):
        if self._is_internet_available():
            if self.timer == 12:
                self.weather_response = requests.get(self.weather_url).json()
                self.timer = 0
            else:
                self.timer += 1

    def on_ui_update(self, ui):
        try:
            tempk = self.weather_response['main']['feels_like']
            tempc = round(tempk - 273.15, 1)
            description = self.weather_response['weather'][0]['main']
            seticon = self.weather_response['weather'][0]['icon']
            source_path = os.path.join(self.plugin_dir, "weather", f"{seticon}.png")
            if seticon != self.previous_seticon:
                logging.info(f"Copying icon from {source_path}")
                if os.path.exists(source_path):
                    shutil.copy(source_path, os.path.join(self.plugin_dir, "weather", "display.png"))
                else:
                    ui.set('main', 'WTHR: Icon Not Found')
                self.previous_seticon = seticon
            ui.set('feels', f"TEMP:{tempc}°C")
            ui.set('main', f"WTHR:{description}")
        except Exception as e:
            ui.set('main', 'WTHR: Error')
            ui.set('feels', 'Temp: Error')

    def on_unload(self, ui):
        with ui._lock:
            ui.remove_element('feels')
            ui.remove_element('main')
            logging.info("Weather Plugin unloaded")