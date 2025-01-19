# goto openweathermap.org and get an api key and cityid.
# gps requires gpsdeasy to be installed
#main.plugins.weather2pwn.enabled = true # enable plugin weather2pwn
#main.plugins.weather2pwn.log = False # log the weather data
#main.plugins.weather2pwn.cityid = "CITY_ID" # set the cityid
#main.plugins.weather2pwn.getbycity = false # get the weather data from gps or cityid by default(gps falls back to cityid if not available)
#main.plugins.weather2pwn.api_key = "API_KEY" # openweathermap.org api key
#main.plugins.weather2pwn.decimal = "true" # include 2 decimal places for the temperature
#main.plugins.weather2pwn.units = "c" or "f" to determine celsius or fahrenheit
#main.plugins.weather2pwn.displays = [ "city", "temp", "sky", ] # display these values on the screen

import socket, json, requests, logging, os, time, toml, subprocess, datetime
from pwnagotchi.ui.components import LabeledValue
from pwnagotchi.ui.view import BLACK
import pwnagotchi.ui.fonts as fonts
import pwnagotchi.plugins as plugins
import pwnagotchi

class Weather2Pwn(plugins.Plugin):
    __author__ = 'NeonLightning'
    __version__ = '2.4.5'
    __license__ = 'GPL3'
    __description__ = 'Weather display from gps data or city id, with optional logging'

    def on_ready(self, agent):
        self.running = True
        time.sleep(15)
        self.loaded = True
        logging.info("[Weather2Pwn] Ready")

    def _is_internet_available(self):
        try:
            socket.create_connection(("www.google.com", 80), timeout=3)
            return True
        except OSError:
            return False

    def ensure_gpsd_running(self):
        try:
            result = subprocess.run(['pgrep', '-x', 'gpsd'], stdout=subprocess.PIPE)
            if result.returncode != 0 or result.returncode != None:
                return True
            else:
                return False
        except Exception as e:
            logging.exception(f"[Weather2Pwn] Error ensuring gpsd is running: {e}")
            return False

    def get_weather_by_city_id(self):
        try:
            base_url = "http://api.openweathermap.org/data/2.5/weather"
            complete_url = f"{base_url}?id={self.city_id}&appid={self.api_key}&units=metric&lang=en-US"
            response = requests.get(complete_url)
            if response.status_code == 200:
                data = response.json()
                self.errortries = 0
                return data
            else:
                while self.errortries == 3:
                    logging.info(f"[Weather2Pwn] Error fetching weather data attempt {self.errortries}")
                    time.sleep(1)
                    self.errortries += 1
                    self.get_weather_by_city_id()
                logging.error(f"[Weather2Pwn] Error fetching weather data: {response.text}")
                self.errortries = 0
                return None
        except Exception as e:
            while self.errortries == 3:
                logging.info(f"[Weather2Pwn] Error fetching weather data attempt {self.errortries}")
                time.sleep(1)
                self.errortries += 1
                self.get_weather_by_city_id()
            logging.error(f"[Weather2Pwn] Exception fetching weather data: {e}")
            self.errortries = 0
            return None
        
    def get_location_data(self, server_url):
        try:
            response = requests.get(server_url)
            response.raise_for_status()  # Raise an exception for HTTP errors
            return response.json()  # Parse the JSON response
        except requests.exceptions.RequestException as e:
            logging.warning(f"Error connecting to the server: {e}")
            return None
        
    def get_gps_coordinates(self):
        if self.pwndroid:
            logging.info(f"[Weather2Pwn] attempting Pwndroid")
            server_url = f"http://192.168.44.1:8080"
            location_data = self.get_location_data(server_url)
            if location_data:
                return location_data.get("latitude", 0), location_data.get("longitude", 0)
            else:
                logging.warning("[Weather2Pwn] Failed to retrieve PwnDroid coordinates.")
                return 0, 0
        else:
            logging.info(f"[Weather2Pwn] attempting gpsd")
            if not self.ensure_gpsd_running():
                return 0, 0
            else:
                try:
                    gpsd_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    gpsd_socket.connect(('localhost', 2947))
                    gpsd_socket.sendall(b'?WATCH={"enable":true,"json":true}\n')
                    time.sleep(2)
                    for _ in range(6):
                        data = gpsd_socket.recv(4096).decode('utf-8')
                        for line in data.splitlines():
                            try:
                                report = json.loads(line)
                                if report['class'] == 'TPV' and 'lat' in report and 'lon' in report:
                                    return report['lat'], report['lon']
                            except json.JSONDecodeError:
                                logging.warning('[Weather2Pwn] Failed to decode JSON response.')
                                continue
                        logging.debug('[Weather2Pwn] No GPS data found in this attempt.')
                        time.sleep(0.5)
                    logging.debug('[Weather2Pwn] No GPS data found.')
                    return 0, 0
                except Exception as e:
                    logging.exception(f"[Weather2Pwn] Error getting GPS coordinates: {e}")
                    return 0, 0
                finally:
                    gpsd_socket.close()

    def get_weather_by_gps(self, lat, lon, api_key):
        try:
            base_url = "http://api.openweathermap.org/data/2.5/weather"
            complete_url = f"{base_url}?lat={lat}&lon={lon}&units=metric&lang=en-us&appid={api_key}"
            response = requests.get(complete_url)
            if response.status_code == 200:
                self.errortries = 0
                return response.json()
            else:
                while self.errortries == 3:
                    logging.info(f"[Weather2Pwn] Error fetching weather data attempt {self.errortries}")
                    time.sleep(1)
                    self.errortries += 1
                    self.get_weather_by_gps
                logging.error(f"[Weather2Pwn] Error fetching weather data: {response.status_code}")
                self.errortries = 0
                return None
        except Exception as e:
            while self.errortries == 3:
                logging.info(f"[Weather2Pwn] Error fetching weather data attempt {self.errortries}")
                time.sleep(1)
                self.errortries += 1
                self.get_weather_by_gps
            logging.exception(f"[Weather2Pwn] Exception fetching weather data: {e}")
            self.errortries = 0
            return None

    def store_weather_data(self):
        if self.weather_log == True:
            self.current_date = datetime.datetime.now().strftime("%Y-%m-%d")
            file_path = f'/root/weather/weather2pwn_data_{self.current_date}.json'
            directory = "/root/weather/"
            logging.info(f"[Weather2Pwn] Logging to {file_path}")
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
        else:
            pass

    def on_loaded(self):
        logging.info("[Weather2Pwn] loading")
        self.displays = self.options.get('displays', '[ "city", "temp", "sky", ]')
        self.units = self.options.get('units', '"c"')
        self.decimal = self.options.get('decimal', 'true')
        self.pwndroid = self.options.get('pwndroid', 'false')
        self.api_key = self.options.get('api_key', '""')
        self.getbycity = self.options.get('getbycity', 'true')
        self.city_id = self.options.get('cityid', '')
        self.weather_log = self.options.get('log', 'true')
        self.logged_lat, self.logged_long = 0, 0
        self.last_fetch_time = time.time()
        self.inetcount = 3
        self.fetch_interval = 5
        self.firstrun = True
        self.errortries = 0
        self.weather_data = {}
        self.current_date = datetime.datetime.now().strftime("%Y-%m-%d")
        self.running = False
        self.checkgps_time = 0
        self.ui_update_time = time.time()
        if os.path.exists('/tmp/weather2pwn_data.json'):
            os.remove('/tmp/weather2pwn_data.json')
        logging.info("[Weather2Pwn] Plugin loaded.")

    def on_ui_setup(self, ui):
        if 'city' in self.displays:
            pos1 = (150, 37)
            ui.add_element('city', LabeledValue(color=BLACK, label='', value='loading',
                                                position=pos1,
                                                label_font=fonts.Small, text_font=fonts.Small))
        if 'temp' in self.displays:
            pos2 = (155, 47)
            ui.add_element('feels_like', LabeledValue(color=BLACK, label='Tmp:', value='loading',
                                                    position=pos2,
                                                    label_font=fonts.Small, text_font=fonts.Small))
        if 'sky' in self.displays:
            pos3 = (155, 57)
            ui.add_element('weather', LabeledValue(color=BLACK, label='Sky :', value='loading',
                                                    position=pos3,
                                                    label_font=fonts.Small, text_font=fonts.Small))

    def _update_weather(self):
        if self._is_internet_available():
            latitude, longitude = 0, 0
            current_time = time.time()
            if (current_time - self.checkgps_time) >= (self.fetch_interval / 2):
                latitude, longitude = self.get_gps_coordinates()
                logging.debug(f"[Weather2Pwn] Latitude diff: {abs(self.logged_lat - latitude)}, Longitude diff: {abs(self.logged_long - longitude)}, inetcount: {self.inetcount}, last: {self.checkgps_time} current: {current_time} fetch: {self.fetch_interval} gpstime: {self.checkgps_time} diff: {current_time - self.checkgps_time}")
                self.checkgps_time = current_time
            if (current_time - self.last_fetch_time >= self.fetch_interval or abs(self.logged_lat - latitude) >= 0.01 or abs(self.logged_long - longitude) > 0.01):
                if abs(self.logged_lat - latitude) >= 0.005 or abs(self.logged_long - longitude) >= 0.005 or (current_time - self.last_fetch_time >= self.fetch_interval):
                    self.inetcount += 1
                try:
                    if abs(self.logged_lat - latitude) >= 0.01 or abs(self.logged_long - longitude) >= 0.01 or self.inetcount >= 2:
                        if self.getbycity == False:
                            latitude, longitude = self.get_gps_coordinates()
                            if latitude != 0 and longitude != 0 or not latitude and longitude:
                                logging.info(f"[Weather2Pwn] GPS data found. {latitude}, {longitude}")
                                self.weather_data = self.get_weather_by_gps(latitude, longitude, self.api_key)
                                if self.weather_data is not None:
                                    self.weather_data["name"] = self.weather_data["name"] + " *GPS*"
                                logging.info("[Weather2Pwn] weather setup by gps")
                                self.last_fetch_time = current_time
                            else:
                                logging.info(f"[Weather2Pwn] GPS data not found.")
                                self.weather_data = self.get_weather_by_city_id()
                                if not self.weather_data:
                                    logging.info("[Weather2Pwn] no weather data found")
                                else:
                                    logging.info("[Weather2Pwn] weather setup by city")
                                self.last_fetch_time = current_time
                        else:
                            self.weather_data = self.get_weather_by_city_id()
                            if self.weather_data:
                                if self.weather_data is not None:
                                    logging.info("[Weather2Pwn] weather setup by city")
                            else:
                                logging.info("[Weather2Pwn] no weather data found")
                            self.last_fetch_time = current_time
                        if os.path.exists('/tmp/weather2pwn_data.json'):
                            with open('/tmp/weather2pwn_data.json', 'r') as f:
                                self.weather_data = json.load(f)
                        if self.weather_data:
                            self.store_weather_data()
                            self.logged_lat = latitude
                            self.logged_long = longitude
                            self.inetcount = 0
                except Exception as e:
                    logging.exception(f"[Weather2pwn] An error occurred {e}")
                    logging.exception(f"[Weather2pwn] An error occurred2 {self.weather_data}")
                self.readycheck = False

    def on_ui_update(self, ui):
        if self.running:
            current_time = time.time()
            if current_time - self.last_fetch_time >= self.fetch_interval:
                if self._is_internet_available():
                    if self.loaded == True:
                        self._update_weather()
                        self.fetch_interval = self.options.get('fetch_interval', '1800')
                        if os.path.exists('/tmp/weather2pwn_data.json'):
                            with open('/tmp/weather2pwn_data.json', 'r') as f:
                                self.weather_data = json.load(f)
                        if self.weather_data:
                            if "name" in self.weather_data:
                                city_name = self.weather_data["name"]
                                if 'city' in self.displays:
                                    ui.set('city', f"{city_name}")
                            if "main" in self.weather_data and "feels_like" in self.weather_data["main"]:
                                feels_like = self.weather_data["main"]["feels_like"]
                                if 'temp' in self.displays: 
                                    if not self.decimal:
                                        feels_like = round(feels_like)
                                    if self.units == "c":
                                        ui.set('feels_like', f"{feels_like}°C")
                                    elif self.units == "f":
                                        feels_like = (feels_like * 9/5) + 32
                                        feels_like = round(feels_like)
                                        ui.set('feels_like', f"{feels_like}°F")
                            if "weather" in self.weather_data and len(self.weather_data["weather"]) > 0:
                                main_weather = self.weather_data["weather"][0]["main"]
                                if 'sky' in self.displays:
                                    ui.set('weather', f"{main_weather}")
                else:
                    self.fetch_interval = 180
                    if 'city' in self.displays:
                        ui.set('city', 'No Network')
                    if 'temp' in self.displays:
                        ui.set('feels_like', '')
                    if 'sky' in self.displays:
                        ui.set('weather', '')

    def on_unload(self, ui):
        self.running = False
        if os.path.exists("/tmp/weather2pwn_data.json"):
            os.remove("/tmp/weather2pwn_data.json")
        with ui._lock:
            for element in ['city', 'feels_like', 'weather']:
                try:
                    ui.remove_element(element)
                except KeyError:
                    pass
            logging.info("[Weather2Pwn] Unloaded")