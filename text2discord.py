import logging
import requests
import pwnagotchi
import pwnagotchi.plugins as plugins
import time
import os

class Text2Discord(plugins.Plugin):
    __author__ = 'NeonLightning'
    __version__ = '0.0.3'
    __license__ = 'GPL3'
    __description__ = '''
                    Sends the output of specific text and png files out to Discord.
                    '''

    def __init__(self):
        logging.debug("[*] Out2Discord plugin created")
        self.last_line_numbers = {}
        self.last_message_time = None
        self.last_bot_message_time = None
        
    def check_last_bot_message_time(self):
        webhook_url = pwnagotchi.config['main']['plugins']['out2discord']['webhook']
        response = requests.get(webhook_url)
        if response.status_code == 200:
            messages = response.json()
            for message in reversed(messages):
                if message['author']['id'] == pwnagotchi.config['main']['plugins']['out2discord']['bot_id']:
                    self.last_bot_message_time = message['timestamp']
                    break
        else:
            logging.warning(f"Failed to check last bot message time: {response.text}")

    def on_loaded(self):
        self.loaded = True
        logging.info(f"O2D Loaded")
        self.main_loop()
        
    def on_unload(self, ui):
        self.loaded = False
        logging.info(f"O2D Unloaded")

    def should_send(self):
        wait_time = pwnagotchi.config['main']['plugins']['out2discord']['wait_time']
        if self.last_message_time is None:
            return True
        elif time.time() - self.last_message_time > wait_time:
            return True
        else:
            return False

    def main_loop(self):
        while self.loaded:
            if self.should_send():
                self.main_send()
                self.last_message_time = time.time()
            time.sleep(10)
        
    def main_send(self):
        self.file_paths = pwnagotchi.config['main']['plugins']['out2discord']['files']
        for file_path in self.file_paths:
            self.last_line_numbers[file_path] = 0

        for file_path in self.file_paths:
            try:
                if not os.path.exists(file_path):
                    logging.warning(f"File not found: {file_path}")
                    continue

                with open(file_path, 'r') as f:
                    lines = f.readlines()
                    msg = ''
                    for line in lines:
                        if len(msg + line) > 2000:
                            data = {'content': msg}
                            webhook_url = pwnagotchi.config['main']['plugins']['out2discord']['webhook']
                            response = requests.post(webhook_url, json=data)
                            if response.status_code != 204:
                                logging.warning(f"Failed to send message to Discord: {msg.strip()}")
                            msg = ''
                        msg += line
                    if msg:
                        data = {'content': msg}
                        webhook_url = pwnagotchi.config['main']['plugins']['out2discord']['webhook']
                        response = requests.post(webhook_url, json=data)
                        if response.status_code != 204:
                            logging.warning(f"Failed to send message to Discord: {msg.strip()}")
                            
                    time.sleep(5)
            except Exception as e:
                logging.warning(f"An error occurred while processing the file: {file_path}. Error: {str(e)}")

        # send png files
        pngs_dir = pwnagotchi.config['main']['plugins']['out2discord']['pngs']
        if isinstance(pngs_dir, str):
            pngs_dir = [pngs_dir]
        for dir_path in pngs_dir:
            if os.path.isdir(dir_path):
                for filename in os.listdir(dir_path):
                    if filename.endswith(".png"):
                        try:
                            file_path = os.path.join(dir_path, filename)
                            with open(file_path, 'rb') as f:
                                data = {
                                    'content': f"{filename}"
                                }
                                response = requests.post(
                                    pwnagotchi.config['main']['plugins']['out2discord']['webhook'],
                                    json=data
                                )
                                if response.status_code != 204:
                                    logging.warning(f"Failed to send message to Discord: {data['content']}")
                                else:
                                    logging.info(f"Sent message to Discord: {data['content']}")

                                with open(file_path, 'rb') as f:
                                    data = {
                                        'file': (filename, f, 'image/png')
                                    }
                                    response = requests.post(
                                        pwnagotchi.config['main']['plugins']['out2discord']['webhook'],
                                        files=data
                                    )
                                    if response.status_code != 200:
                                        logging.warning(f"Failed to send image to Discord: {file_path}. Response code: {response.status_code}. Response text: {response.text}")
                                    else:
                                        logging.info(f"Sent image to Discord: {file_path}")

                        except Exception as e:
                            logging.warning(f"An error occurred while processing the file: {file_path}. Error: {str(e)}")
                            
                        time.sleep(3)
            else:
                logging.warning(f"{dir_path} is not a directory")

