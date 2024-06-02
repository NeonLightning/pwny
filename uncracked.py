import logging, os, glob, pwnagotchi
import pwnagotchi.plugins as plugins
from flask import abort, send_from_directory, render_template_string, request, send_file

TEMPLATE = """
{% extends "base.html" %}
{% set active_page = "handshakes" %}
{% block title %}
    {{ title }}
{% endblock %}
{% block styles %}
    {{ super() }}
    <style>
        #filter {
            width: 100%;
            font-size: 16px;
            padding: 12px 20px 12px 40px;
            border: 1px solid #ddd;
            margin-bottom: 12px;
        }
    </style>
{% endblock %}
{% block script %}
    var shakeList = document.getElementById('list');
    var filter = document.getElementById('filter');
    var filterVal = filter.value.toUpperCase();
    filter.onkeyup = function() {
        document.body.style.cursor = 'progress';
        var table, tr, tds, td, i, txtValue;
        filterVal = filter.value.toUpperCase();
        li = shakeList.getElementsByTagName("li");
        for (i = 0; i < li.length; i++) {
            txtValue = li[i].textContent || li[i].innerText;
            if (txtValue.toUpperCase().indexOf(filterVal) > -1) {
                li[i].style.display = "list-item";
            } else {
                li[i].style.display = "none";
            }
        }
        document.body.style.cursor = 'default';
    }
{% endblock %}
{% block content %}
    <input type="text" id="filter" placeholder="Search for ..." title="Type in a filter">
    <ul id="list" data-role="listview" style="list-style-type:disc;">
        {% for handshake in handshakes %}
            {% for ext in handshake.ext %}
                <li class="file">
                    <a href="/plugins/uncracked/{{handshake.name}}{{ext}}">{{handshake.name}}{{ext}}</a>
                </li>
            {% endfor %}
        {% endfor %}
    </ul>
{% endblock %}
"""

class Handshake:
    def __init__(self, name, path, ext):
        self.name = name
        self.path = path
        self.ext = ext

class Uncracked(plugins.Plugin):
    __author__ = 'NeonLightning'
    __version__ = '1.0.0'
    __license__ = 'GPL3'
    __description__ = 'Download handshake not found in wpa-sec from web-ui.'

    def __init__(self):
        self.ready = False

    def on_loaded(self):
        logging.info("[Uncracked] plugin loaded")

    def on_config_changed(self, config):
        self.config = config
        self.ready = True

    def read_potfile(self):
        potfile_path = os.path.join(self.config['bettercap']['handshakes'], "wpa-sec.cracked.potfile")
        try:
            with open(potfile_path, 'r') as file_in:
                lines = file_in.readlines()
            return set(line.split(":")[2:4] for line in lines if line.strip())
        except FileNotFoundError:
            logging.error("[Uncracked] potfile not found")
            return set()
        except Exception as e:
            logging.error(f"[Uncracked] error reading potfile: {e}")
            return set()

    def find_uncracked_handshakes(self, unique_lines):
        handshakes = []
        try:
            for ext in ['.pcap', '.2500', '.16800', '.22000']:
                pcapfiles = glob.glob(os.path.join(self.config['bettercap']['handshakes'], f"*{ext}"))
                for path in pcapfiles:
                    name = os.path.basename(path)[:-len(ext)]
                    fullpathNoExt = path[:-len(ext)]
                    if not any(f"{ssid}_{bssid}" in name for ssid, bssid in unique_lines):
                        handshakes.append(Handshake(name, fullpathNoExt, [ext]))
            handshakes = sorted(handshakes, key=lambda x: x.name.lower())
        except Exception as e:
            logging.error(f"[Uncracked] error finding uncracked handshakes: {e}")
        return handshakes

    def on_webhook(self, path, request):
        try:
            if not self.ready:
                return "Plugin not ready"
            if path == "/" or not path:
                logging.info(f"[Uncracked] Loaded webhook")
                unique_lines = self.read_potfile()
                data = self.find_uncracked_handshakes(unique_lines)
                return render_template_string(TEMPLATE, title="Handshakes | " + pwnagotchi.name(), handshakes=data)
            else:
                logging.info(f"[Uncracked] serving {dir}/{path}")
                return self.serve_file(path)
        except Exception as e:
            logging.error(f"[Uncracked] error in webhook: {e}")
            abort(500)

    def serve_file(self, path):
        dir = self.config['bettercap']['handshakes']
        try:
            logging.info(f"[Uncracked] serving {dir}/{path}")
            return send_from_directory(directory=dir, path=path, as_attachment=True)
        except FileNotFoundError:
            logging.error(f"[Uncracked] file not found: {path}")
            abort(404)
        except Exception as e:
            logging.error(f"[Uncracked] error serving file: {e}")
            abort(500)