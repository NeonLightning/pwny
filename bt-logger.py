import pwnagotchi, logging, re, subprocess, io, socket, json
import pwnagotchi.plugins as plugins
from pwnagotchi.ui.components import LabeledValue
from pwnagotchi.ui.view import BLACK
import pwnagotchi.ui.fonts as fonts

class BTLog(plugins.Plugin):
    __author__ = 'NeonLightning'
    __version__ = '1.0.0'
    __license__ = 'GPL3'
    __description__ = 'Logs and displays a count of bluetooth devices seen.'

    def on_loaded(self):
        self._agent = None
        self._ui = None
        if self.options.get('gps') is not None:
            self.gps = self.options.get('gps')
        else:
            self.gps = False
        self.check_and_update_config('main.plugins.bt-logger.gps', 'false')
        self.count = 0
        self.interim_file = '/root/.btinterim.log'
        self.output = '/root/bluetooth.log'
        try:
            with open(self.output, 'r') as log_file:
                if isinstance(log_file, io.TextIOBase):
                    self.count = sum(1 for line in log_file)
        except FileNotFoundError:
            with open(self.output, 'w'):
                self.count = 0
                pass
        logging.info('[BT-Log] Loaded')
        self.running = True
        self.log_bluetooth_scan(self.output, self.interim_file)

    def on_unload(self, ui):
        self.running = False
        with ui._lock:
            try:
                ui.remove_element('bt-log')
            except KeyError:
                pass
        logging.info('[BT-Log] Unloaded')
        
    def on_ready(self, agent):
        self._agent = agent
        
    def on_ui_setup(self, ui):
        self._ui = ui
        try:
            ui.add_element('bt-log', LabeledValue(color=BLACK, label='BT#:', value='0', position=(0, 80),
                                        label_font=fonts.Small, text_font=fonts.Small))
        except:
            logging.error(f"[BT-Log] UI not made")

    def on_ui_update(self, ui):
        try:
            with open(self.output, 'r') as log_file:
                if isinstance(log_file, io.TextIOBase):
                    self.count = sum(1 for line in log_file)
        except FileNotFoundError:
            self.count = 0
            with open(self.output, 'w'):
                pass
        ui.set('bt-log', str(self.count))
        
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

    def check_and_update_config(self, key, value):
        config_file = '/etc/pwnagotchi/config.toml'
        try:
            with open(config_file, 'r') as f:
                config_lines = f.readlines()
            key_found = False
            insert_index = -1
            for i, line in enumerate(config_lines):
                if 'main.plugins.bt-logger.enabled' in line:
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
                logging.info(f"[BT-Log] Added {key} to the config file with value {value}")
        except Exception as e:
            logging.error(f"[BT-Log] Exception occurred while processing config file: {e}")
            
    def remove_ansi_escape_sequences(self, text):
        ansi_escape = re.compile(r'\x1B[@-_][0-?]*[ -/]*[@-~]|\x1B\[.*?[@-~]|\^A\^B')
        return ansi_escape.sub('', text)

    def log_bluetooth_scan(self, output_file, interim_file):
        device_pattern = re.compile(r'NEW.*Device ([0-9A-F:]{17}) (.+)')
        with open(output_file, 'a') as log_file:
            process = subprocess.Popen(['bluetoothctl'], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE, universal_newlines=True)
            process.stdin.write('scan on\n')
            process.stdin.flush()
            while self.running:
                clean_output = self.remove_ansi_escape_sequences(process.stdout.readline())
                match = device_pattern.search(clean_output)
                if match:
                    mac_address = match.group(1)
                    device_name = match.group(2)
                    entry = f"{device_name} {mac_address}"
                    if not self.is_duplicate(entry, interim_file):
                        self.count += 1
                        log_entry = f"{entry}"
                        if self._ui:
                            self._ui.set("status", "BT Found\n" + str(entry))
                        latitude, longitude = self.get_gps_coordinates()
                        logging.info(f"[BT-Log] {log_entry}")
                        if self.gps == True:
                            if self.get_gps_coordinates() != None:
                                log_entry = f"{log_entry}: {latitude}, {longitude}\n"
                            else:
                                log_entry = f"{entry}\n"
                                pass
                        else:
                            log_entry = f"{entry}\n"
                            pass
                        log_file.write(log_entry)
                        log_file.flush()
                        with open(interim_file, 'a') as interim:
                            interim.write(f"{entry}\n")
                            interim.flush()

    def is_duplicate(self, entry, interim_file):
        try:
            with open(interim_file, 'r') as interim:
                for line in interim:
                    if line.strip() == entry:
                        return True
            return False
        except FileNotFoundError:
            with open(interim_file, 'w'):
                pass
            return False