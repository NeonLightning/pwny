# gps requires gpsdeasy to be installed
#main.plugins.bt-logger.enabled = true
#main.plugins.bt-logger.gps = true
#main.plugins.bt-logger.gps_track = true
#main.plugins.bt-logger.id_only = true
#main.plugins.bt-logger.display = true

import pwnagotchi, logging, re, subprocess, io, socket, json, time
import pwnagotchi.plugins as plugins
import pwnagotchi.ui.fonts as fonts
from flask import Flask, render_template_string
from pwnagotchi.ui.components import LabeledValue
from pwnagotchi.ui.view import BLACK

class BTLog(plugins.Plugin):
    __author__ = 'NeonLightning'
    __version__ = '1.0.4'
    __license__ = 'GPL3'
    __description__ = 'Logs and displays a count of bluetooth devices seen.'

    def on_loaded(self):
        self.gps = self.options.get('gps', False)
        self.display = self.options.get('display', False)
        self.gps_track = self.options.get('gps_track', True)
        self.id_only = self.options.get('id_only', True)
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
        if self.display == True:
            with ui._lock:
                try:
                    ui.remove_element('bt-log')
                except KeyError:
                    pass
        logging.info('[BT-Log] Unloaded')
        
    def on_ui_setup(self, ui):
        if self.display == True:
            try:
                ui.add_element('bt-log', LabeledValue(color=BLACK, label='BT#:', value='0', position=(0, 80),
                                            label_font=fonts.Small, text_font=fonts.Small))
            except:
                logging.error(f"[BT-Log] UI not made")

    def on_ui_update(self, ui):
        if self.display == True:
            try:
                with open(self.output, 'r') as log_file:
                    if isinstance(log_file, io.TextIOBase):
                        self.count = sum(1 for line in log_file)
            except FileNotFoundError:
                self.count = 0
                with open(self.output, 'w'):
                    pass
            ui.set('bt-log', str(self.count))
        
    def on_webhook(self, path, request):
        logging.info(f"Received webhook request for path: {path}")
        log_file_path = '/root/bluetooth.log'
        devices = []
        try:
            with open(log_file_path, 'r') as log_file:
                for line in log_file:
                    match = re.match(r'(.+) ([0-9A-F:]+): (-?\d+\.\d+), (-?\d+\.\d+)', line)
                    if match:
                        device_name, mac_address, latitude, longitude = match.groups()
                        devices.append({
                            'name': device_name,
                            'mac': mac_address,
                            'latitude': latitude,
                            'longitude': longitude
                        })
        except FileNotFoundError:
            logging.error("Bluetooth log file not found")
            pass
        template = '''
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta http-equiv="X-UA-Compatible" content="IE=edge">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Bluetooth Devices</title>
                <style>
                    table {
                        width: 100%;
                        border-collapse: collapse;
                    }
                    th, td {
                        border: 1px solid black;
                        padding: 8px;
                        text-align: left;
                    }
                    th {
                        background-color: #f2f2f2;
                    }
                </style>
            </head>
            <body>
                <h1>Bluetooth Devices</h1>
                <table>
                    <thead>
                        <tr>
                            <th>Name</th>
                            <th>MAC Address</th>
                            <th>Google Maps</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for device in devices %}
                            <tr>
                                <td>{{ device.name }}</td>
                                <td>{{ device.mac }}</td>
                                <td>
                                    <a href="https://www.google.com/maps/search/?api=1&query={{ device.latitude }},{{ device.longitude }}">{{ device.latitude }} {{ device.longitude }}</a>
                                </td>
                            </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </body>
            </html>
        '''
        return render_template_string(template, devices=devices)

    def ensure_gpsd_running(self):
        try:
            result = subprocess.run(['pgrep', '-x', 'gpsd'], stdout=subprocess.PIPE)
            if result.returncode != 0 or not result.returncode == None:
                return True
            else:
                return False
        except Exception as e:
            logging.exception(f"[BT-Log] Error ensuring gpsd is running: {e}")
            return False

    def get_gps_coordinates(self):
        if not self.ensure_gpsd_running():
            return 0, 0
        else:
            try:
                gpsd_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                gpsd_socket.connect(('localhost', 2947))
                gpsd_socket.sendall(b'?WATCH={"enable":true,"json":true}\n')
                time.sleep(2)
                data = gpsd_socket.recv(4096).decode('utf-8')
                for line in data.splitlines():
                    try:
                        report = json.loads(line)
                        if report['class'] == 'TPV' and 'lat' in report and 'lon' in report:
                            return report['lat'], report['lon']
                    except json.JSONDecodeError:
                        logging.warning('[BT-log] Failed to decode JSON response.')
                        return 0, 0
                return 0, 0
            except Exception as e:
                logging.exception(f"[BT-Log] Error getting GPS coordinates: {e}")
                return 0, 0
            finally:
                gpsd_socket.close()

    def remove_ansi_escape_sequences(self, text):
        ansi_escape = re.compile(r'\x1B[@-_][0-?]*[ -/]*[@-~]|\x1B\[.*?[@-~]|\^A\^B')
        return ansi_escape.sub('', text)

    def log_bluetooth_scan(self, output_file, interim_file):
        device_pattern = re.compile(r'NEW.*Device ([0-9A-F:]{17}) (.+)')
        hex_pattern = re.compile(r'^[0-9A-F]{2}-[0-9A-F]{2}-[0-9A-F]{2}-[0-9A-F]{2}-[0-9A-F]{2}-[0-9A-F]{2}$')

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
                    if not self.is_duplicate(entry, interim_file, latitude, longitude) and (not self.id_only or not hex_pattern.search(device_name)):
                        latitude, longitude = self.get_gps_coordinates()
                        if not self.is_duplicate(entry, interim_file, latitude, longitude) and (not self.id_only or not hex_pattern.search(device_name)):
                            self.count += 1
                            log_entry = f"{entry}"
                            logging.info(f"[BT-Log] {log_entry}")
                            if self.gps:
                                if latitude is not None and longitude is not None:
                                    log_entry = f"{log_entry}: {latitude}, {longitude}\n"
                                else:
                                    log_entry = f"{entry}: 0, 0\n"
                            else:
                                log_entry = f"{entry}\n"
                            log_file.write(log_entry)
                            log_file.flush()
                            with open(interim_file, 'a') as interim:
                                interim.write(f"{entry} {latitude} {longitude}\n")
                                interim.flush()
                            self.organize_bluetooth_log(output_file)

    def is_duplicate(self, entry, interim_file, latitude, longitude):
        try:
            with open(interim_file, 'r') as interim:
                for line in interim:
                    logged_entry, logged_latitude, logged_longitude = line.rsplit(' ', 2)
                    if logged_entry == entry:
                        try:
                            logged_latitude = float(logged_latitude)
                            logged_longitude = float(logged_longitude)
                            if latitude is None and longitude is None:
                                if logged_latitude == 0 and logged_longitude == 0:
                                    return True
                            else:
                                if abs(logged_latitude - latitude) < 0.005 and abs(logged_longitude - longitude) < 0.005:
                                    return True
                        except ValueError:
                            continue
            return False
        except FileNotFoundError:
            with open(interim_file, 'w'):
                pass
            return False

    def organize_bluetooth_log(self, output_file):
        hex_pattern = re.compile(r'^[0-9A-F]{2}-[0-9A-F]{2}-[0-9A-F]{2}-[0-9A-F]{2}-[0-9A-F]{2}-[0-9A-F]{2}$')
        try:
            with open(output_file, 'r') as f:
                lines = f.readlines()
            matching_lines = [line for line in lines if hex_pattern.search(line.split()[0])]
            non_matching_lines = [line for line in lines if not hex_pattern.search(line.split()[0])]
            matching_lines.sort()
            non_matching_lines.sort()
            organized_lines = non_matching_lines + matching_lines
            with open(output_file, 'w') as f:
                f.writelines(organized_lines)
            logging.debug('[BT-Log] Organized bluetooth.log')
        except Exception as e:
            logging.error(f"[BT-Log] Error organizing bluetooth.log: {e}")