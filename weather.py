###
# main.plugins.weather.enabled = true
# main.plugins.weather.api_key = ""
# https://home.openweathermap.org/api_keys
# main.plugins.weather.areacode = "postal/zip"
# main.plugins.weather.countrycode = "countrycode"
# main.plugins.weather.gps = "/dev/ttyACM0"
#(even if you don't have a gps set this...)

import os, logging, re, pwnagotchi, toml, json, requests, urllib.request
from pwnagotchi import plugins, config
import pwnagotchi.ui.components as components
import pwnagotchi.ui.view as view
import pwnagotchi.ui.fonts as fonts
import pwnagotchi.plugins as plugins
from pwnagotchi.bettercap import Client

agent = Client('localhost', port=8081, username="pwnagotchi", password="pwnagotchi");    

class WeatherForecast(plugins.Plugin):
    __author__ = 'NeonLightning'
    __version__ = '0.3.0'
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
        self.api_key = None
        self.areacode = None
        self.country = None
        self.lat = None
        self.lon = None
        self.cords = None
        self.timer = 12
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
            ui.set('feels', f"TEMP:{tempc}°C")
            ui.set('main', f"WTHR:{description}")
        except:
            ui.set('main', f"WTHR:NA")
            ui.set('feels', "Temp:NA")

    def on_unload(self, ui):
        with ui._lock:
            ui.remove_element('feels')
            ui.remove_element('main')
            logging.info("Weather Plugin unloaded")