###
# main.plugins.weather.enabled = true
# main.plugins.weather.api_key = ""
# https://home.openweathermap.org/api_keys
# main.plugins.weather.areacode = "postal or zip"
# main.plugins.weather.countrycode = "countrycode"
# (disabled for now)hmain.plugins.weather.gpson = true or false
# (disabled for now)but if you want gps for weather you'll need gps.py or gps_more.py

import logging, pwnagotchi, json, requests, urllib.request
from pwnagotchi import plugins, config
import pwnagotchi.ui.components as components
import pwnagotchi.ui.view as view
import pwnagotchi.ui.fonts as fonts
import pwnagotchi.plugins as plugins
from pwnagotchi.ui.components import Text
from pwnagotchi.bettercap import Client

#agent = Client('localhost', port=8081, username="pwnagotchi", password="pwnagotchi");

class WeatherForecast(plugins.Plugin):
    __author__ = 'NeonLightning'
    __version__ = '1.4.0'
    __license__ = 'GPL3'
    __description__ = 'A plugin that displays the weather forecast on the pwnagotchi screen.'
    __name__ = 'WeatherForecast'

    def _is_internet_available(self):
        try:
            urllib.request.urlopen('https://www.google.com', timeout=0.5)
            return True
        except urllib.request.URLError:
            return False
        
    def on_loaded(self):
        self.areacode = None
        self.country = None
        self.lat = None
        self.lon = None
        self.cords = None
        self.weather_response = None
        self.api_key = config['main']['plugins']['weather']['api_key']
        self.areacode = config['main']['plugins']['weather']['areacode']
        self.country = config['main']['plugins']['weather']['countrycode']
        # self.gpson = config['main']['plugins']['weather']['gpson']
        self.gpson = False
        self.geo_url = f"http://api.openweathermap.org/geo/1.0/zip?zip={self.areacode},{self.country}&appid={self.api_key}"

    def on_ready(self, agent):
        self.timer = 12
        if self._is_internet_available():
                self._update_lat_lon()
                self.weather_response = requests.get(self.weather_url).json()
                logging.info("Weather Ready")

    def _update_lat_lon(self):
        if self.gpson == True:
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
                pass
        else:
            logging.debug("weather update location gps disabled")
            try:
                geo_response = requests.get(self.geo_url).json()
                self.lat = geo_response.get('lat')
                self.lon = geo_response.get('lon')
            except Exception as err:
                logging.error(f"Error fetching latitude:{self.lat} and longitude:{self.lon} error:{err}")
        self.weather_url = f"https://api.openweathermap.org/data/2.5/weather?lat={self.lat}&lon={self.lon}&appid={self.api_key}"
        logging.debug (f"weather url: {self.weather_url}")
        if self._is_internet_available():
            self.weather_response = requests.get(self.weather_url).json()

    def on_ui_setup(self, ui):      
        ui.add_element('feels', components.LabeledValue(color=view.BLACK, label='', value='',
                                                                   position=(90, 85), label_font=fonts.Small, text_font=fonts.Small))
        ui.add_element('main', components.LabeledValue(color=view.BLACK, label='', value='',
                                                            position=(90, 100), label_font=fonts.Small, text_font=fonts.Small))
        self._update_lat_lon()
        logging.debug("Weather ui set")
    
    def on_epoch(self, agent, epoch, epoch_data):
        if self._is_internet_available():
            if self.timer >= 12:
                self.weather_response = requests.get(self.weather_url).json()
                self.timer = 0
                logging.info("Weather Updated")
            else:
                self.timer += 1

    def on_ui_update(self, ui):
        try:
            if 'main' in self.weather_response:
                tempk = self.weather_response['main']['feels_like']
                tempc = round(tempk - 273.15, 1)
                description = self.weather_response['weather'][0]['main']
                ui.set('feels', f"TEMP:{tempc}°C")
                ui.set('main', f"WTHR:{description}")
        except Exception as e:
            ui.set('main', 'WTHR: Error')
            ui.set('feels', f'Temp: {e}')
            logging.exception(f"Weather ERROR: {e}")

    def on_unload(self, ui):
        with ui._lock:
            try:
                ui.remove_element('feels')
            except KeyError:
                pass
            try:
                ui.remove_element('main')
            except KeyError:
                pass
            logging.info("Weather Plugin unloaded")