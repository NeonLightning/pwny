###
# main.plugins.weather.enabled = true
# main.plugins.weather.api_key = ""
# https://home.openweathermap.org/api_keys
# main.plugins.weather.location = ""
# i just guessed location format....

import os, logging, re, subprocess, pwnagotchi, toml, json, requests, urllib.request
from io import TextIOWrapper
from pwnagotchi import plugins, config
import pwnagotchi.ui.components as components
import pwnagotchi.ui.view as view
import pwnagotchi.ui.fonts as fonts
import pwnagotchi.plugins as plugins

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
        self.timer = 12
        self.api_key = None
        self.location = None
        self.weather_response = None
        self.api_key = config['main']['plugins']['weather']['api_key']
        logging.info(f"Weather Forecast Plugin api.{self.api_key}")
        self.location = config['main']['plugins']['weather']['location']
        logging.info(f"Weather Forecast Plugin location.{self.location}")
        self.weather_url = f"https://api.openweathermap.org/data/2.5/weather?q={self.location}&units=metric&appid={self.api_key}"
        if self._is_internet_available():
            self.weather_response = requests.get(self.weather_url).json()

    def on_ui_setup(self, ui):
        ui.add_element('feels', components.LabeledValue(color=view.BLACK, label='', value='',
                                                                   position=(90, 85), label_font=fonts.Small, text_font=fonts.Small))
        ui.add_element('main', components.LabeledValue(color=view.BLACK, label='', value='',
                                                            position=(90, 100), label_font=fonts.Small, text_font=fonts.Small))
    
    def on_internet_available(self):
        if self.timer == 12:
            self.weather_response = requests.get(self.weather_url).json()
            self.timer = 0
            logging.info(f"WF self.timer {self.timer}")
        else:
            self.timer += 1
            logging.info(f"WF self.timer {self.timer}")
                    
    def on_ui_update(self, ui):
        try:
            current_temp = self.weather_response['main']['feels_like']
            description = self.weather_response['weather'][0]['description']
            ui.set('feels', f"TEMP:{current_temp}°C")
            ui.set('main', f"WTHR:{description}")
        except:
            ui.set('main', f"WTHR:NA")
            ui.set('feels', "Temp:NA")

    def on_unload(self, ui):
        with ui._lock:
            ui.remove_element('feels')
            ui.remove_element('main')
            logging.info("Weather Plugin unloaded")