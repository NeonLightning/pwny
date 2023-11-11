<<<<<<< HEAD
import os
import logging
import re
import subprocess
from io import TextIOWrapper
from pwnagotchi import plugins
from pwnagotchi.utils import StatusFile
import requests
import pwnagotchi.ui.components as components
import pwnagotchi.ui.view as view
import pwnagotchi.ui.fonts as fonts
import pwnagotchi.plugins as plugins
import pwnagotchi
import pwnagotchi.ui.fonts as fonts
import pwnagotchi.plugins as plugins
import datetime
import toml
import yaml
import json

class WeatherForecast(plugins.Plugin):
    __author__ = 'Bauke Molenaar'
    __version__ = '1.0.0'
    __license__ = 'GPL3'
    __description__ = 'A plugin that displays the weather forecast on the pwnagotchi screen.'
    __name__ = 'WeatherForecast'
    __help__ = """
    A plugin that displays the weather forecast on the pwnagotchi screen.
    """
    __dependencies__ = {
        'pip': ['scapy'],
    }
    __defaults__ = {
        'enabled': False,
    }

    def on_loaded(self):
        logging.info("Weather Forecast Plugin loaded.")

    def on_ui_setup(self, ui):
        config_is_toml = True if os.path.exists(
            '/etc/pwnagotchi/config.toml') else False
        config_path = '/etc/pwnagotchi/config.toml'
        with open(config_path) as f:
            data = toml.load(f) if config_is_toml else yaml.load(
                f, Loader=yaml.FullLoader)
        ui.add_element('feels', components.LabeledValue(color=view.BLACK, label='', value='',
                                                                   position=(90, 85), label_font=fonts.Small, text_font=fonts.Small))
        ui.add_element('main', components.LabeledValue(color=view.BLACK, label='', value='',
                                                            position=(90, 100), label_font=fonts.Small, text_font=fonts.Small))
    def on_ui_update(self, ui):
        location = "Thunder Bay"
        api_key = "3d34a7f2abb93ca1fd5a5e4aa28db151"
        weather_url = f"https://api.openweathermap.org/data/2.5/weather?q={location}&units=metric&appid={api_key}"
        try:
            weather_response = requests.get(weather_url).json()
            current_temp = weather_response['main']['feels_like']
            description = weather_response['weather'][0]['description']  # Access the first item in the 'weather' list
            ui.set('feels', f"TEMP:{current_temp}°C")
            ui.set('main', f"WTHR:{description}")
        except:
            ui.set('feels', "Temp:NA")

    def on_unload(self, ui):
        with ui._lock:
            ui.remove_element('feels')
            ui.remove_element('main')
=======
import os
import logging
import re
import subprocess
from io import TextIOWrapper
from pwnagotchi import plugins
from pwnagotchi.utils import StatusFile
import requests
import pwnagotchi.ui.components as components
import pwnagotchi.ui.view as view
import pwnagotchi.ui.fonts as fonts
import pwnagotchi.plugins as plugins
import pwnagotchi
import pwnagotchi.ui.fonts as fonts
import pwnagotchi.plugins as plugins
import datetime
import toml
import yaml
import json

class WeatherForecast(plugins.Plugin):
    __author__ = 'Bauke Molenaar'
    __version__ = '1.0.0'
    __license__ = 'GPL3'
    __description__ = 'A plugin that displays the weather forecast on the pwnagotchi screen.'
    __name__ = 'WeatherForecast'
    __help__ = """
    A plugin that displays the weather forecast on the pwnagotchi screen.
    """
    __dependencies__ = {
        'pip': ['scapy'],
    }
    __defaults__ = {
        'enabled': False,
    }

    def on_loaded(self):
        logging.info("Weather Forecast Plugin loaded.")

    def on_ui_setup(self, ui):
        config_is_toml = True if os.path.exists(
            '/etc/pwnagotchi/config.toml') else False
        config_path = '/etc/pwnagotchi/config.toml'
        with open(config_path) as f:
            data = toml.load(f) if config_is_toml else yaml.load(
                f, Loader=yaml.FullLoader)
        ui.add_element('feels', components.LabeledValue(color=view.BLACK, label='', value='',
                                                                   position=(90, 85), label_font=fonts.Small, text_font=fonts.Small))
        ui.add_element('main', components.LabeledValue(color=view.BLACK, label='', value='',
                                                            position=(90, 100), label_font=fonts.Small, text_font=fonts.Small))
    def on_ui_update(self, ui):
        location = "Thunder Bay"
        api_key = "3d34a7f2abb93ca1fd5a5e4aa28db151"
        weather_url = f"https://api.openweathermap.org/data/2.5/weather?q={location}&units=metric&appid={api_key}"
        try:
            weather_response = requests.get(weather_url).json()
            current_temp = weather_response['main']['feels_like']
            description = weather_response['weather'][0]['description']  # Access the first item in the 'weather' list
            ui.set('feels', f"TEMP:{current_temp}°C")
            ui.set('main', f"WTHR:{description}")
        except:
            ui.set('feels', "Temp:NA")

    def on_unload(self, ui):
        with ui._lock:
            ui.remove_element('feels')
            ui.remove_element('main')
            logging.info("Weather Plugin unloaded")