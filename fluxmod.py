# set these to 24hr time values
# main.plugins.fluxmod.invert_on_time = "20:00"
# main.plugins.fluxmod.invert_off_time = "6:00"

import toml, os, threading, logging, subprocess
from datetime import datetime, time
from pwnagotchi import plugins

class Fluxmod(plugins.Plugin):
    __author__ = 'NeonLightning'
    __version__ = '1.0.0'
    __license__ = 'GPL3'
    __description__ = 'Changes ui.invert on a timer'

    def on_loaded(self):
        self.config_path = '/etc/pwnagotchi/config.toml'
        self.invert_on_time = None
        self.invert_off_time = None
        self.stop_event = threading.Event()
        logging.info('[fluxmod] Fluxmod plugin loaded')
        self.load_config()
        self.thread = threading.Thread(target=self.run)
        self.thread.start()

    def on_unload(self, _):
        self.stop_event.set()
        self.thread.join()
        logging.info('[fluxmod] Fluxmod plugin unloaded')

    def load_config(self):
        try:
            with open(self.config_path, 'r') as f:
                config = toml.load(f)
            self.invert_on_time = datetime.strptime(config['main']['plugins']['fluxmod']['invert_on_time'], '%H:%M').time()
            self.invert_off_time = datetime.strptime(config['main']['plugins']['fluxmod']['invert_off_time'], '%H:%M').time()
            logging.info(f'[fluxmod] Configuration loaded: invert_on_time={self.invert_on_time}, invert_off_time={self.invert_off_time}')
        except Exception as e:
            logging.error(f'[fluxmod] Error loading configuration: {e}')
            self.invert_on_time = time(20, 0)
            self.invert_off_time = time(6, 0)
            logging.info(f'[fluxmod] Using default times: invert_on_time={self.invert_on_time}, invert_off_time={self.invert_off_time}')

    def run(self):
        while not self.stop_event.is_set():
            self.update_invert_ui()
            self.stop_event.wait(30)

    def update_invert_ui(self):
        try:
            now = datetime.now().time()
            if self.invert_on_time <= self.invert_off_time:
                invert = self.invert_on_time <= now <= self.invert_off_time
            else:
                invert = now >= self.invert_on_time or now <= self.invert_off_time
            logging.debug(f'[fluxmod] Inversion status: {invert}')
            config_file = '/etc/pwnagotchi/config.toml'
            with open(config_file, 'r') as f:
                config_lines = f.readlines()
            for i, line in enumerate(config_lines):
                if 'ui.invert' in line:
                    if str(invert).lower() not in line.lower():
                        config_lines[i] = f'ui.invert = {str(invert).lower()}\n'
                        with open(config_file, 'w') as f:
                            f.writelines(config_lines)
                        os.system('sudo systemctl restart pwnagotchi')
                        logging.info(f'[fluxmod] Updated ui.invert to {invert}')
                    break
        except Exception as e:
            logging.error(f'[fluxmod] Error updating ui.invert: {e}')

if __name__ == "__main__":
    config_file = '/etc/pwnagotchi/config.toml'
    try:
        with open(config_file, 'r') as f:
            config_lines = f.readlines()
        invert = None
        for i, line in enumerate(config_lines):
            if 'ui.invert' in line:
                invert = 'true' if 'false' in line.lower() else 'false'
                config_lines[i] = f'ui.invert = {invert}\n'
                break
        if invert is None:
            raise ValueError("ui.invert not found in config file")
        for i, line in enumerate(config_lines):
            if 'main.plugins.fluxmod.enabled = true' in line:
                config_lines[i] = 'main.plugins.fluxmod.enabled = false\n'
        with subprocess.Popen(['sudo', 'tee', config_file], stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) as proc:
            proc.stdin.write(''.join(config_lines).encode())
        os.system('sudo systemctl restart pwnagotchi')
        print(f"[fluxmod] Toggled ui.invert to {invert}")
    except Exception as e:
        print(f"[fluxmod] Error updating config: {e}")
