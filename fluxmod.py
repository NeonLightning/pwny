# set these to 24hr time values
# main.plugins.fluxmod.invert_on_time = "20:00"
# main.plugins.fluxmod.invert_off_time = "6:00"
import toml, os, threading, logging, subprocess
from datetime import datetime, time
from pwnagotchi import plugins

class Fluxmod(plugins.Plugin):
    __author__ = 'NeonLightning'
    __version__ = '1.0.3'
    __license__ = 'GPL3'
    __description__ = 'Changes ui.invert on a timer'

    def on_loaded(self):
        self.config_path = '/etc/pwnagotchi/config.toml'
        self.stop_event = threading.Event()
        self.load_config()
        self.thread = threading.Thread(target=self.run)
        self.thread.start()
        logging.info('[fluxmod] Fluxmod plugin loaded')

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
            invert = self.should_invert(now)
            if self.update_config(invert):
                logging.info(f'[fluxmod] Updated ui.invert to {invert}')
                os.system('sudo systemctl restart pwnagotchi')
        except Exception as e:
            logging.error(f'[fluxmod] Error updating ui.invert: {e}')

    def should_invert(self, current_time):
        if self.invert_on_time <= self.invert_off_time:
            return self.invert_on_time <= current_time <= self.invert_off_time
        return current_time >= self.invert_on_time or current_time <= self.invert_off_time

    def update_config(self, invert):
        try:
            with open(self.config_path, 'r') as f:
                config_lines = f.readlines()
            current_invert = None
            new_invert = 'true' if invert else 'false'
            for i, line in enumerate(config_lines):
                if 'ui.invert' in line:
                    if 'true' in line.lower():
                        current_invert = 'true'
                    elif 'false' in line.lower():
                        current_invert = 'false'
                    if current_invert != new_invert:
                        config_lines[i] = f'ui.invert = {new_invert}\n'
                    break
            if current_invert != new_invert:
                with open(self.config_path, 'w') as f:
                    f.writelines(config_lines)
                return True
            return False
        except Exception as e:
            logging.error(f'[fluxmod] Error reading/writing config file: {e}')
            return False

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