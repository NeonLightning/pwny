#goto openweathermap.org and get an api key and cityid.
#main.plugins.weather2pwn.enabled = true
#main.plugins.weather2pwn.log = False
#main.plugins.weather2pwn.fetch_interval = 3600
#main.plugins.weather2pwn.cityid = "CITY_ID"
#main.plugins.weather2pwn.getbycity = false
#main.plugins.weather2pwn.api_key = "API_KEY"
#main.plugins.weather2pwn.gps = "/dev/ttyACM0"
#main.plugins.weather2pwn.log = False

import socket, json, requests, logging, os, time, toml, subprocess, datetime
from pwnagotchi.ui.components import LabeledValue
from pwnagotchi.ui.view import BLACK
import pwnagotchi.ui.fonts as fonts
import pwnagotchi.plugins as plugins

class Weather2Pwn(plugins.Plugin):
    __author__ = 'NeonLightning'
    __version__ = '1.1.2'
    __license__ = 'GPL3'
    __description__ = 'Weather display from gps data or city id, with optional logging'

    def __init__(self):
        self.config_path = '/etc/pwnagotchi/config.toml'
        self.check_and_update_config('main.plugins.weather2pwn.fetch_interval', '3600')
        self.check_and_update_config('main.plugins.weather2pwn.api_key', '""')
        self.check_and_update_config('main.plugins.weather2pwn.getbycity', 'false')
        self.check_and_update_config('main.plugins.weather2pwn.cityid', '""')
        self.check_and_update_config('main.plugins.weather2pwn.gps', '"/dev/ttyUSB0"')
        self.check_and_update_config('main.plugins.weather2pwn.log', 'false')
        try:
            with open(self.config_path, 'r') as f:
                config = toml.load(f)
                self.fetch_interval = config['main']['plugins']['weather2pwn']['fetch_interval']
                self.api_key = config['main']['plugins']['weather2pwn']['api_key']
                self.getbycity = config['main']['plugins']['weather2pwn']['getbycity']
                self.getbycity = self.getbycity in [True, 'true', 'True']
                self.city_id = config['main']['plugins']['weather2pwn']['cityid']
                self.gps_device = config['main']['plugins']['weather2pwn']['gps']
                self.weather_log = config['main']['plugins']['weather2pwn']['log']
                self.weather_log = self.weather_log in [True, 'true', 'True']
                self.language = config['main']['lang']
        except Exception as e:
            logging.exception(f'[Weather2Pwn] Error loading configuration: {e}')
        file_path = f'/root/weather/weather2pwn_tmp_data.json'
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                for line in f:
                    data = json.loads(line)
                    data_time = datetime.datetime.strptime(data['time'], "%Y-%m-%d %H:%M")
                    current_time = datetime.datetime.now()
                    time_diff = current_time - data_time
                    if abs(time_diff.total_seconds()) == 3600:
                        self.logged_long = data['lon']
                        self.logged_lat = data['lat']
                    else:
                        self.logged_lat, self.logged_long = 0, 0
        else:
            self.logged_lat, self.logged_long = 0, 0
        self.last_fetch_time = 0
        self.inetcount = 0
        self.weather_data = {}
        self.current_date = datetime.datetime.now().strftime("%Y-%m-%d")

    def _is_internet_available(self):
        try:
            socket.create_connection(("www.google.com", 80))
            return True
        except OSError:
            return False
        
    def ensure_gpsd_running(self):
        try:
            result = subprocess.run(['pgrep', '-x', 'gpsd'], stdout=subprocess.PIPE)
            if result.returncode != 0:
                logging.info("[Weather2Pwn] Starting gpsd...")
                subprocess.run(['sudo', 'gpsd', self.gps_device, '-F', '/var/run/gpsd.sock'])
                time.sleep(2)
        except Exception as e:
            logging.exception(f"[Weather2Pwn] Error ensuring gpsd is running: {e}")
            return False
        return True

    def get_weather_by_city_id(self, lang):
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
        if not self.ensure_gpsd_running():
            return 0, 0
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
            logging.exception(f"[Weather2Pwn] Error getting GPS coordinates: {e}")
            return 0, 0

    def get_weather_by_gps(self, lat, lon, api_key, lang):
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
            logging.exception(f"[Weather2Pwn] Exception fetching weather data: {e}")
            return None

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
            logging.exception(f"[Weather2Pwn] Exception occurred while processing config file: {e}")

    def store_weather_data(self):
        logging.debug(f"[Weather2Pwn] logging {self.weather_log}")
        if self.weather_log == True:
            self.current_date = datetime.datetime.now().strftime("%Y-%m-%d")
            file_path = f'/root/weather/weather2pwn_data_{self.current_date}.json'
            directory = "/root/weather/"
            tmp_file_path = '/root/weather/weather2pwn_tmp_data.json'
            logging.info(f"[Weather2Pwn] Logging to {file_path}")
            tmp_data = {
                "time": time.strftime("%Y-%m-%d %H:%M"),
                "lon": self.weather_data.get('coord', {}).get('lon'),
                "lat": self.weather_data.get('coord', {}).get('lat')
            }
            data_to_store = {
                "time": time.strftime("%Y-%m-%d %H:%M:%S"),
                "weather_data": self.weather_data
            }
            try:
                os.makedirs(directory, exist_ok=True)
                with open(file_path, 'a') as f:
                    f.write(json.dumps(data_to_store) + '\n')
                logging.info("[Weather2Pwn] Weather data stored successfully.")
            except Exception as e:
                logging.exception(f"[Weather2Pwn] Error storing weather data: {e}")
            try:
                os.makedirs(directory, exist_ok=True)
                with open(tmp_file_path, 'w+') as f:
                    f.write(json.dumps(tmp_data) + '\n')
                logging.debug("[Weather2Pwn] Weather data location stored successfully.")
            except Exception as e:
                logging.exception(f"[Weather2Pwn] Error storing weather data location: {e}")
        else:
            pass

    def on_loaded(self):
        logging.info("[Weather2Pwn] loading")
        if os.path.exists('/tmp/weather2pwn_data.json'):
            os.remove('/tmp/weather2pwn_data.json')
        logging.info("[Weather2Pwn] Plugin loaded.")
        logging.debug(f"[Weather2Pwn] getbycity {self.getbycity}")

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
        if self._is_internet_available():
            try:
                if self.getbycity == False:
                    latitude, longitude = self.get_gps_coordinates()
                    if latitude and longitude:
                        self.weather_data = self.get_weather_by_gps(latitude, longitude, self.api_key, self.language)
                        self.weather_data["name"] = self.weather_data["name"] + " *GPS*"
                        logging.info("[Weather2Pwn] weather setup by gps initially")
                    else:
                        self.weather_data = self.get_weather_by_city_id(self.language)
                        self.logged_long = self.weather_data['lon']
                        self.logged_lat = self.weather_data['lat']
                        longitude = self.weather_data['lon']
                        latitude = self.weather_data['lat']
                        logging.info("[Weather2Pwn] weather setup by city initially")
                else:
                    self.weather_data = self.get_weather_by_city_id(self.language)
                    self.logged_long = self.weather_data['lon']
                    self.logged_lat = self.weather_data['lat']
                    longitude = self.weather_data['lon']
                    latitude = self.weather_data['lat']
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
                    logging.info("[Weather2Pwn] storing on startup...")
                    self.store_weather_data()
            except Exception as e:
                logging.exception(f"[Weather2pwn] An error occurred {e}")
                logging.exception(f"[Weather2pwn] An error occurred2 {self.weather_data}")
        else:
            current_time = time.time()
            if current_time - self.last_fetch_time >= self.fetch_interval:
                ui.set('city', 'No Network')
                ui.set('feels_like', '')
                ui.set('weather', '')

    def on_internet_available(self, agent):
        current_time = time.time()
        latitude, longitude = self.get_gps_coordinates()
        if current_time - self.last_fetch_time >= self.fetch_interval or abs(self.logged_lat - latitude) > 0.005 or abs(self.logged_long - longitude) > 0.005:
            if self.getbycity == False:
                if abs(self.logged_lat - latitude) > 0.005 or abs(self.logged_long - longitude) > 0.005:
                    logging.debug("[Weather2Pwn] moved past previous location")
                    logging.debug(f"[Weather2Pwn] location {latitude} {longitude}")
                    logging.debug(f"[Weather2Pwn] prevlocation {self.logged_lat} {self.logged_long}")
                else:
                    logging.debug("[Weather2Pwn] moved past timeout")
                logging.debug('[Weather2Pwn] getbycity false on Internet')
                try:
                    if latitude and longitude:
                        self.weather_data = self.get_weather_by_gps(latitude, longitude, self.api_key, self.language)
                        if self.weather_data:
                            with open('/tmp/weather2pwn_data.json', 'w') as f:
                                self.weather_data["name"] = self.weather_data["name"] + " *GPS*"
                                json.dump(self.weather_data, f)
                            self.logged_lat, self.logged_long = latitude, longitude
                            if abs(self.logged_lat - latitude) > 0.005 or abs(self.logged_long - longitude) > 0.005 or self.inetcount == 2:
                                if self.inetcount == 2:
                                    logging.info("[Weather2Pwn] storing on second count...")
                                    self.store_weather_data()
                                    self.inetcount = 0
                                elif abs(self.logged_lat - latitude) > 0.005 or abs(self.logged_long - longitude) > 0.005:
                                    logging.info("[Weather2Pwn] storing on movement...")
                                    self.store_weather_data()
                                    self.inetcount = 0
                            self.inetcount += 1
                            logging.info(f"[Weather2Pwn] GPS Weather data obtained successfully.")
                        else:
                            self.weather_data = self.get_weather_by_city_id(self.language)
                            if self.weather_data:
                                logging.info(f"[Weather2Pwn] City Weather data obtained successfully.")
                            else:
                                if os.path.exists('/tmp/weather2pwn_data.json'):
                                    os.remove('/tmp/weather2pwn_data.json')
                                logging.error("[Weather2Pwn] Failed to fetch weather data.")
                            self.logged_long = self.weather_data['lon']
                            self.logged_lat = self.weather_data['lat']
                            longitude = self.weather_data['lon']
                            latitude = self.weather_data['lat']
                            if self.inetcount == 2:
                                if self.inetcount == 2:
                                    logging.info("[Weather2Pwn] storing on second count...")
                                self.store_weather_data()
                                self.inetcount = 0
                            self.inetcount += 1
                    else:
                        if os.path.exists('/tmp/weather2pwn_data.json'):
                            os.remove('/tmp/weather2pwn_data.json')
                        self.logged_lat, self.logged_long = 0, 0
                        logging.error("[Weather2Pwn] GPS coordinates not obtained.")
                except Exception as e:
                    logging.exception(f"[Weather2Pwn] error setting weather on internet {e}")
            else:
                self.weather_data = self.get_weather_by_city_id(self.language)
                if self.weather_data:
                    self.logged_long = self.weather_data['lon']
                    self.logged_lat = self.weather_data['lat']
                    longitude = self.weather_data['lon']
                    latitude = self.weather_data['lat']
                    if self.inetcountry == 2:
                        self.store_weather_data()
                        self.inetcount = 0
                    self.inetcount += 1
                    logging.info(f"[Weather2Pwn] City Weather data obtained successfully.")
                else:
                    if os.path.exists('/tmp/weather2pwn_data.json'):
                        os.remove('/tmp/weather2pwn_data.json')
                    logging.error("[Weather2Pwn] Failed to fetch weather data.")           
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