#goto openweathermap.org and get an api key.
#setup main.plugins.weather2pwn.api_key = "apikey from openweathermap.org"
#if you lack a gps or don't want to use itsetup main.plugins.weather2pwn.getbycity = "true"
# also for getbycity set main.plugins.weather2pwn.city_id = "city id on openweathermap.org"
#depends on gpsd and clients installed
import socket, json, requests, logging, os, time, toml
from pwnagotchi.ui.components import LabeledValue
from pwnagotchi.ui.view import BLACK
import pwnagotchi.ui.fonts as fonts
import pwnagotchi.plugins as plugins
class Weather2Pwn(plugins.Plugin):
    __author__ = 'NeonLightning'
    __version__ = '1.0.4'
    __license__ = 'GPL3'
    __description__ = 'Weather display from location data'

    def _is_internet_available(self):
        try:
            socket.create_connection(("www.google.com", 80))
            return True
        except OSError:
            return False

    def get_weather_by_city_id(self, lang="en"):
        try:
            base_url = "http://api.openweathermap.org/data/2.5/weather"
            complete_url = f"{base_url}?id={self.city_id}&appid={self.api_key}&units=metric&lang={lang}"
            response = requests.get(complete_url)
            if response.status_code == 200:
                data = response.json()
                return data
            else:
                logging.error(f"[Weather2Pwn] Error fetching weather data: {response.status_code}")
                if os.path.exists('/tmp/weather2pwn_data.json'):
                    os.remove('/tmp/weather2pwn_data.json')
                return None
        except Exception as e:
            if os.path.exists('/tmp/weather2pwn_data.json'):
                os.remove('/tmp/weather2pwn_data.json')
            logging.error(f"[Weather2Pwn] Exception fetching weather data: {e}")
            return None

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

    def get_weather_by_gps(self, lat, lon, api_key, lang="en"):
        try:
            base_url = "http://api.openweathermap.org/data/2.5/weather"
            complete_url = f"{base_url}?lat={lat}&lon={lon}&units=metric&lang={lang}&appid={api_key}"
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
            if self.getbycity == False:
                latitude, longitude = self.get_gps_coordinates()
                if latitude and longitude:
                    self.weather_data = self.get_weather_by_gps(latitude, longitude, self.api_key)
                    if self.weather_data:
                        with open('/tmp/weather2pwn_data.json', 'w') as f:
                            json.dump(self.weather_data, f)
                        self.weather_data["name"] = self.weather_data["name"] + " *GPS*"
                        logging.info("[Weather2Pwn] Initial weather data obtained successfully.")
                    else:
                        self.weather_data = self.get_weather_by_city_id()
                        if self.weather_data:
                            logging.info(f"[Weather2Pwn] Weather data obtained successfully.")
                        else:
                            if os.path.exists('/tmp/weather2pwn_data.json'):
                                os.remove('/tmp/weather2pwn_data.json')
                            logging.error("[Weather2Pwn] Failed to fetch weather data.")
                else:
                    logging.error("[Weather2Pwn] GPS coordinates not obtained.")
            else:
                self.weather_data = self.get_weather_by_city_id()

    def check_and_update_config(self, key, value):
        config_file = '/etc/pwnagotchi/config.toml'
        try:
            with open(config_file, 'r') as f:
                config_lines = f.readlines()
            key_found = False
            insert_index = -1
            for i, line in enumerate(config_lines):
                if 'main.plugins.weather2pwn.enabled' in line:
                    key_found = True
                    insert_index = i + 1
                    break
            key_found = False
            for line in config_lines:
                if key in line:
                    key_found = True
                    break
            if not key_found:
                config_lines.insert(insert_index, f"{key} = {value}\n")
                with open(config_file, 'w') as f:
                    f.writelines(config_lines)
                logging.info(f"[Weather2Pwn] Added {key} to the config file with value {value}")
        except Exception as e:
            logging.error(f"[Weather2Pwn] Exception occurred while processing config file: {e}")

    def on_loaded(self):
        logging.info("[Weather2Pwn] loading")
        self.internet_counter = 0
        if os.path.exists('/tmp/weather2pwn_data.json'):
            os.remove('/tmp/weather2pwn_data.json')
        self.check_and_update_config('main.plugins.weather2pwn.fetch_interval', '3600')
        self.check_and_update_config('main.plugins.weather2pwn.api_key', '""')
        self.check_and_update_config('main.plugins.weather2pwn.getbycity', 'false')
        self.check_and_update_config('main.plugins.weather2pwn.cityid', '""')
        self.fetch_interval = self.options.get('fetch_interval', '3600')
        self.api_key = self.options.get('api_key', '')
        getbycity_option = self.options.get('getbycity', 'false')
        if isinstance(getbycity_option, bool):
            self.getbycity = getbycity_option
        else:
            self.getbycity = getbycity_option.lower() == 'true'
        self.city_id = self.options.get('city_id', '')
        self.last_fetch_time = 0
        self.weather_data = None
        logging.info("[Weather2Pwn] Plugin loaded.")

    def on_agent(self, agent) -> None:
        self.on_internet_available(self, agent)

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

    def on_internet_available(self, agent):
        current_time = time.time()
        if current_time - self.last_fetch_time >= self.fetch_interval:
            if self.getbycity == False:
                latitude, longitude = self.get_gps_coordinates()
                if latitude and longitude:
                    self.weather_data = self.get_weather_by_gps(latitude, longitude, self.api_key)
                    if self.weather_data:
                        with open('/tmp/weather2pwn_data.json', 'w') as f:
                            self.weather_data["name"] = self.weather_data["name"] + " *GPS*"
                            json.dump(self.weather_data, f)
                        logging.info(f"[Weather2Pwn] Weather data obtained successfully.")
                    else:
                        weather_data = weather2pwn.get_weather_by_city_id()
                        if self.weather_data:
                            logging.info(f"[Weather2Pwn] Weather data obtained successfully.")
                        else:
                            if os.path.exists('/tmp/weather2pwn_data.json'):
                                os.remove('/tmp/weather2pwn_data.json')
                            logging.error("[Weather2Pwn] Failed to fetch weather data.")
                else:
                    if os.path.exists('/tmp/weather2pwn_data.json'):
                        os.remove('/tmp/weather2pwn_data.json')
                    logging.error("[Weather2Pwn] GPS coordinates not obtained.")
            else:
                self.weather_data = self.get_weather_by_city_id()
            self.last_fetch_time = current_time

    def on_ui_update(self, ui):
        if self._is_internet_available():
            if os.path.exists('/tmp/weather2pwn_data.json'):
                with open('/tmp/weather2pwn_data.json', 'r') as f:
                    self.weather_data = json.load(f)
            if self.weather_data:
                if "name" in self.weather_data:
                    city_name = self.weather_data["name"]
                    ui.set('city', f"{city_name}")
                if "main" in self.weather_data and "feels_like" in self.weather_data["main"]:
                    feels_like = self.weather_data["main"]["feels_like"]
                    ui.set('feels_like', f"{feels_like}°C")
                if "weather" in self.weather_data and len(self.weather_data["weather"]) > 0:
                    main_weather = self.weather_data["weather"][0]["main"]
                    ui.set('weather', f"{main_weather}")
        else:
            current_time = time.time()
            if current_time - self.last_fetch_time >= self.fetch_interval:
                ui.set('city', 'No Network')
                ui.set('feels_like', '')
                ui.set('weather', '')

    def on_unload(self, ui):
        with ui._lock:
            for element in ['city', 'feels_like', 'weather']:
                try:
                    ui.remove_element(element)
                except KeyError:
                    pass
            logging.info("[Weather2Pwn] Unloaded")

if __name__ == "__main__":
    config_file = '/etc/pwnagotchi/config.toml'
    try:
        with open(config_file, 'r') as f:
            config = toml.load(f)
        weather_config = config.get('main', {}).get('plugins', {}).get('weather2pwn', {})
        api_key = weather_config.get('api_key', '')
        getbycity = weather_config.get('getbycity', False)
        city_id = weather_config.get('city_id', '')
        weather2pwn = Weather2Pwn()
        weather2pwn.api_key = api_key
        weather2pwn.getbycity = getbycity
        weather2pwn.city_id = city_id
        if weather2pwn._is_internet_available():
            if getbycity:
                weather_data = weather2pwn.get_weather_by_city_id()
            else:
                latitude, longitude = weather2pwn.get_gps_coordinates()
                if latitude and longitude:
                    weather_data = weather2pwn.get_weather_by_gps(latitude, longitude, api_key)
                else:
                    weather_data = weather2pwn.get_weather_by_city_id()
                    print("[Weather2Pwn] GPS coordinates not obtained.")
                    weather_data = None
            if weather_data:
                with open('/tmp/weather2pwn_data.json', 'w') as f:
                    json.dump(weather_data, f)
                print("[Weather2Pwn] Weather data obtained successfully.")
            else:
                if os.path.exists('/tmp/weather2pwn_data.json'):
                    os.remove('/tmp/weather2pwn_data.json')
                print("[Weather2Pwn] Failed to fetch weather data.")
        else:
            if os.path.exists('/tmp/weather2pwn_data.json'):
                os.remove('/tmp/weather2pwn_data.json')
            print("[Weather2Pwn] No internet connection available.")
    except Exception as e:
        if os.path.exists('/tmp/weather2pwn_data.json'):
            os.remove('/tmp/weather2pwn_data.json')
        print(f"[Weather2Pwn] Exception occurred: {e}")
