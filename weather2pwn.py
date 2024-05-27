import socket
import json
import requests
import logging
from pwnagotchi.ui.components import LabeledValue
from pwnagotchi.ui.view import BLACK
import pwnagotchi.ui.fonts as fonts
import pwnagotchi.plugins as plugins

class Weather2Pwn(plugins.Plugin):
    __author__ = 'NeonLightning'
    __version__ = '0.0.1'
    __license__ = 'GPL3'
    __description__ = 'weather display from locdata'

    def _is_internet_available(self):
        try:
            socket.create_connection(("www.google.com", 80))
            return True
        except OSError:
            return False

    def get_gps_coordinates(self):
        try:
            gpsd_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            gpsd_socket.connect(('localhost', 2947))
            gpsd_socket.sendall(b'?WATCH={"enable":true,"json":true}')

            while True:
                data = gpsd_socket.recv(4096).decode('utf-8')
                for line in data.splitlines():
                    try:
                        report = json.loads(line)
                        if report['class'] == 'TPV' and 'lat' in report and 'lon' in report:
                            return report['lat'], report['lon']
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            logging.error(f"[Weather2Pwn] Error getting GPS coordinates: {e}")
            return None, None

    def get_weather_by_gps(self, lat, lon, api_key, units="metric", lang="en"):
        try:
            base_url = "http://api.openweathermap.org/data/2.5/weather"
            complete_url = f"{base_url}?lat={lat}&lon={lon}&units={units}&lang={lang}&appid={api_key}"
            response = requests.get(complete_url)
            if response.status_code == 200:
                return response.json()
            else:
                logging.error(f"[Weather2Pwn] Error fetching weather data: {response.status_code}")
                return None
        except Exception as e:
            logging.error(f"[Weather2Pwn] Exception fetching weather data: {e}")
            return None
        
    def on_ready(self, agent):
        if self._is_internet_available():
            logging.info("[Weather2Pwn] Internet is available.")
            latitude, longitude = self.get_gps_coordinates()
            if latitude and longitude:
                logging.info(f"[Weather2Pwn] GPS coordinates obtained: {latitude}, {longitude}")
                self.weather_data = self.get_weather_by_gps(latitude, longitude, self.api_key)
                if self.weather_data:
                    logging.info("[Weather2Pwn] Weather data obtained successfully.")
                else:
                    logging.error("[Weather2Pwn] Failed to fetch weather data.")
            
    def on_loaded(self):
        self.api_key = self.options['api_key']
        logging.info("[Weather2Pwn] Plugin loaded.")

    def on_ui_setup(self, ui):
        pos1 = (150, 37)
        ui.add_element('city', LabeledValue(color=BLACK, label='', value='',
                                            position=pos1,
                                            label_font=fonts.Small, text_font=fonts.Small))
        pos2 = (155, 47)
        ui.add_element('feels_like', LabeledValue(color=BLACK, label='Temp:', value='',
                                                position=pos2,
                                                label_font=fonts.Small, text_font=fonts.Small))
        pos3 = (155, 57)
        ui.add_element('weather', LabeledValue(color=BLACK, label='Sky :', value='',
                                                position=pos3,
                                                label_font=fonts.Small, text_font=fonts.Small))

    def on_internet_available(self):
        logging.info("[Weather2Pwn] Internet is available.")
        latitude, longitude = self.get_gps_coordinates()
        if latitude and longitude:
            logging.info(f"[Weather2Pwn]  lat {latitude}  long {longitude}")
            self.weather_data = self.get_weather_by_gps(latitude, longitude, self.api_key)
            if self.weather_data:
                logging.info("[Weather2Pwn] Weather data obtained successfully.")
            else:
                logging.error("[Weather2Pwn] Failed to fetch weather data.")
 
    def on_ui_update(self, ui):
        if self.weather_data:
            if "name" in self.weather_data:
                city_name = self.weather_data["name"]
                logging.debug(f"[Weather2Pwn] City: {city_name}")
                ui.set('city', f"{city_name}")
            if "main" in self.weather_data and "feels_like" in self.weather_data["main"]:
                feels_like = self.weather_data["main"]["feels_like"]
                logging.debug(f"[Weather2Pwn] Feels Like: {feels_like}")
                ui.set('feels_like', f"{feels_like}°C")
            if "weather" in self.weather_data and len(self.weather_data["weather"]) > 0:
                main_weather = self.weather_data["weather"][0]["main"]
                logging.debug(f"[Weather2Pwn] Weather: {main_weather}")
                ui.set('weather', f"{main_weather}")
                
    def on_unload(self, ui):
        with ui._lock:
            try:
                ui.remove_element('city')
            except KeyError:
                pass
            try:
                ui.remove_element('feels_like')
            except KeyError:
                pass
            try:
                ui.remove_element('weather')
            except KeyError:
                pass
            logging.info("[Weather2Pwn] Unloaded")
