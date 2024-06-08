import pwnagotchi, logging, re, subprocess, io
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
        self.count = 0
        self.interim_file = '/root/.btinterim.log'
        self.output = '/root/bluetooth.log'
        try:
            with open(self.output, 'r') as log_file:
                if isinstance(log_file, io.TextIOBase):
                    self.count = sum(1 for line in log_file)
        except FileNotFoundError:
            with open(self.output, 'w'):
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

    def on_ui_setup(self, ui):
        ui.add_element('bt-log', LabeledValue(color=BLACK, label='BT#:', value=str(self.count), position=(100, 100),
                                        label_font=fonts.Small, text_font=fonts.Small))

    def on_ui_update(self, ui):
        try:
            with open(self.output, 'r') as log_file:
                if isinstance(log_file, io.TextIOBase):
                    self.count = sum(1 for line in log_file)
        except FileNotFoundError:
            with open(self.output, 'w'):
                pass
        ui.set('bt-log', str(self.count))

    def remove_ansi_escape_sequences(self, text):
        ansi_escape = re.compile(r'\x1B[@-_][0-?]*[ -/]*[@-~]|\x1B\[.*?[@-~]|\^A\^B')
        return ansi_escape.sub('', text)

    def log_bluetooth_scan(self, output_file, interim_file):
        device_pattern = re.compile(r'NEW.*Device ([0-9A-F:]{17}) (.+)')
        with open(output_file, 'w') as log_file:
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
                    entry = f"{mac_address} {device_name}"
                    if not self.is_duplicate(entry, interim_file):
                        self.count += 1
                        log_entry = f"{entry}\n"
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