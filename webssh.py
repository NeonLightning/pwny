import subprocess, logging, os, requests
from pwnagotchi import plugins
from flask import request, render_template_string

class WebSSHPlugin(plugins.Plugin):
    __author__ = 'Your Name'
    __version__ = '1.0.0'
    __license__ = 'GPL3'
    __description__ = 'A plugin to run WebSSH based on the client IP address'

    def download_ttyd(self, url, save_path):
        try:
            response = requests.get(url)
            response.raise_for_status()
            ttyd_dir = os.path.dirname(save_path)
            if not os.path.exists(ttyd_dir):
                os.makedirs(ttyd_dir)
            with open(save_path, 'wb') as file:
                file.write(response.content)
            os.chmod(save_path, 0o755)
        except requests.exceptions.HTTPError as e:
            logging.error(f"HTTP error occurred: {e}")
        except requests.exceptions.RequestException as e:
            logging.error(f"An error occurred during the request: {e}")

    def on_loaded(self):
        self.plugin_dir = os.path.dirname(os.path.abspath(__file__))
        self.ttyd_path = os.path.join(self.plugin_dir, 'ttyd', 'ttyd.armhf')
        if not os.path.exists(self.ttyd_path):
            logging.info('Downloading ttyd.armhf...')
            self.download_ttyd("https://github.com/tsl0922/ttyd/releases/download/1.7.7/ttyd.armhf", self.ttyd_path)
        if os.path.exists(self.ttyd_path):
            subprocess.Popen([self.ttyd_path, '--writable', 'bash'])
            logging.info('[WebSSH] plugin loaded')
        else:
            logging.error(f"Failed to find ttyd.armhf at {self.ttyd_path}. Download might have failed.")
        
    def on_unload(self, ui):
        subprocess.Popen(['pkill', 'ttyd.armhf'])
        logging.info('[WebSSH] plugin unloaded')

    def on_webhook(self, path, request):
        try:
            iframe_src = f'http://{request.host.split(":")[0]}:7681'
            template = """
            {% extends "base.html" %}
            {% block content %}
            <div style="display: flex; justify-content: center; align-items: center; height: calc(100vh - 47px);">
                <iframe src="{{ iframe_src }}" title="WebSSH" id="webssh" style="width:calc(80vw); height:calc(80vh);" ></iframe>
            </div>
            {% endblock %}
            """
            return render_template_string(template, iframe_src=iframe_src)
        except Exception as e:
            logging.error(f'Error: {e}')
