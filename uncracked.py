import logging, os, glob, pwnagotchi
import pwnagotchi.plugins as plugins
from flask import abort, send_from_directory, render_template_string, make_response, send_file
import zipfile

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
        }
        .button-container {
            display: flex;
            gap: 10px; /* Space between buttons */
            margin-top: 20px;
        }
        .button-container #download-btn {
            padding: 10px 20px;
            font-size: 16px;
            background-color: #4CAF50;
            color: white;
            border: none;
            cursor: pointer;
        }
        .button-container #download-btn:hover {
            background-color: #45a049;
        }
    </style>
{% endblock %}
{% block script %}
    var shakeList = document.getElementById('list');
    var filter = document.getElementById('filter');
    var currentExtension = "";
    function filterList() {
        document.body.style.cursor = 'progress';
        var li = shakeList.getElementsByTagName("li");
        var filterVal = filter.value.toUpperCase();
        for (var i = 0; i < li.length; i++) {
            var txtValue = li[i].textContent || li[i].innerText;
            var isVisible = li[i].dataset.originalVisible === "true";
            if (isVisible && txtValue.toUpperCase().indexOf(filterVal) > -1) {
                li[i].style.display = "list-item";
            } else {
                li[i].style.display = "none";
            }
        }
        document.body.style.cursor = 'default';
    }
    filter.onkeyup = filterList;
    function filterByExtension(extension) {
        document.body.style.cursor = 'progress';
        var li = shakeList.getElementsByTagName("li");
        currentExtension = extension;
        for (var i = 0; i < li.length; i++) {
            var anchorTag = li[i].querySelector("a");
            if (anchorTag && anchorTag.href.includes(extension)) {
                li[i].style.display = "list-item";
                li[i].dataset.originalVisible = "true";
            } else {
                li[i].style.display = "none";
                li[i].dataset.originalVisible = "false";
            }
        }
        filterList();
        document.body.style.cursor = 'default';
    }
    function resetFilter() {
        document.body.style.cursor = 'progress';
        var li = shakeList.getElementsByTagName("li");
        currentExtension = ""; // Clear the current filter
        for (var i = 0; i < li.length; i++) {
            li[i].style.display = "list-item";
            li[i].dataset.originalVisible = "true";
        }
        filter.value = "";
        document.body.style.cursor = 'default';
    }
    window.onload = function() {
        resetFilter();
    };
    function downloadHandshakes() {
        window.location.href = "/plugins/uncracked/download";
    }
    function downloadHandshakes22000() {
        window.location.href = "/plugins/uncracked/download_22000";
    }
    function downloadHandshakespcap() {
        window.location.href = "/plugins/uncracked/download_pcap";
    }
    function downloadHandshakes16800() {
        window.location.href = "/plugins/uncracked/download_16800";
    }
{% endblock %}
{% block content %}
    <div class="button-container">
        <button id="download-btn" onclick="downloadHandshakes()">Download Uncracked Handshakes</button>
        <button id="download-btn" onclick="downloadHandshakes22000()">Download Uncracked 22000 Handshakes</button>
        <button id="download-btn" onclick="downloadHandshakespcap()">Download Uncracked pcap Handshakes</button>
        <button id="download-btn" onclick="downloadHandshakes16800()">Download Uncracked 16800 Handshakes</button>
    </div>
    <div class="button-container">
        <button id="filter-btn" onclick="filterByExtension('.pcap')">Show Only .pcap</button>
        <button id="filter-btn" onclick="filterByExtension('.22000')">Show Only .22000</button>
        <button id="filter-btn" onclick="filterByExtension('.16800')">Show Only .16800</button>
        <button id="filter-btn" onclick="resetFilter()">Show All</button>
    </div>
    <input type="text" id="filter" placeholder="Search for ...">
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
    __version__ = '1.0.4'
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
            return set(tuple(line.split(":")[2:4]) for line in lines if line.strip())
        except FileNotFoundError:
            logging.error("[Uncracked] potfile not found")
            return set()
        except Exception as e:
            logging.error(f"[Uncracked] error reading potfile: {e}")
            return set()

    def find_uncracked_handshakes(self, unique_lines):
        handshakes = []
        try:
            for ext in ['.pcap', '.16800', '.22000']:
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

    def compress_and_send(self, extension=None):
        logging.info("[Uncracked] Compressing and sending")
        directory_to_compress = self.config['bettercap']['handshakes']
        logging.debug(f"[Uncracked] Compressing and sending {directory_to_compress}")
        zip_suffix = f"_{extension}" if extension else ""
        zip_file_path = f"/tmp/handshakes{zip_suffix}.zip"
        logging.info(f"[Uncracked] Compressing and sending {zip_file_path}")
        default_extensions = ['pcap', '22000', '16800']
        extensions = extension.split(',') if extension else default_extensions
        if os.path.exists(zip_file_path):
            os.remove(zip_file_path)
        try:
            with zipfile.ZipFile(zip_file_path, 'w') as zipf:
                for root, _, files in os.walk(directory_to_compress):
                    for file in files:
                        file_extension = file.split('.')[-1]
                        if file_extension in extensions:
                            file_path = os.path.join(root, file)
                            ssid_bssid_ext = '.'.join(file.split('.')[:-1])
                            if not self.is_in_potfile(ssid_bssid_ext):
                                zipf.write(file_path, os.path.relpath(file_path, directory_to_compress))
                                logging.debug(f"[Uncracked] Added file to zip archive: {file_path}")
            logging.debug(f"[Uncracked] Added files to zip archive")
            response = make_response(send_file(zip_file_path, as_attachment=True))
            response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
            response.headers['Pragma'] = 'no-cache'
            response.headers['Expires'] = '0'
            return response
        except Exception as e:
            logging.error(f"[Uncracked] Error compressing and sending file: {e}")
            abort(500)

    def is_in_potfile(self, ssid_bssid_ext):
        potfile_path = os.path.join(self.config['bettercap']['handshakes'], "wpa-sec.cracked.potfile")
        try:
            with open(potfile_path, 'r') as file_in:
                lines = file_in.readlines()
            lines = [line.strip() for line in lines if line.strip()]
            for line in lines:
                fields = line.split(":")
                ssid = fields[2]
                bssid = fields[0]
                if f"{ssid}_{bssid}" in ssid_bssid_ext:
                    return True
            return False
        except FileNotFoundError:
            logging.error("[Uncracked] potfile not found")
            return False
        except Exception as e:
            logging.error(f"[Uncracked] error reading potfile: {e}")
            return False

    def on_webhook(self, path, request):
        try:
            if not self.ready:
                return "Plugin not ready"
            if path == "/" or not path:
                logging.info(f"[Uncracked] Loaded webhook")
                unique_lines = self.read_potfile()
                data = self.find_uncracked_handshakes(unique_lines)
                return render_template_string(TEMPLATE, title="Handshakes | " + pwnagotchi.name(), handshakes=data)
            elif path == "download":
                logging.debug("[Uncracked] Compressing and sending on webhook")
                return self.compress_and_send()
            elif path == "download_22000":
                logging.debug("[Uncracked] Compressing and sending 22000 on webhook")
                return self.compress_and_send("22000")
            elif path == "download_pcap":
                logging.debug("[Uncracked] Compressing and sending pcap on webhook")
                return self.compress_and_send("pcap")
            elif path == "download_16800":
                logging.debug("[Uncracked] Compressing and sending 16800 on webhook")
                return self.compress_and_send("16800")
            else:
                logging.info(f"[Uncracked] serving {path}")
                return self.serve_file(path)
        except Exception as e:
            logging.error(f"[Uncracked] error in webhook: {e}")
            abort(500)

    def serve_file(self, path):
        dir = self.config['bettercap']['handshakes']
        try:
            logging.info(f"[Uncracked] serving {dir}/{path}")
            response = send_from_directory(directory=dir, path=path, as_attachment=True)
            response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
            response.headers['Pragma'] = 'no-cache'
            response.headers['Expires'] = '0'
            return response
        except FileNotFoundError:
            logging.error(f"[Uncracked] file not found: {path}")
            abort(404)
        except Exception as e:
            logging.error(f"[Uncracked] error serving file: {e}")
            abort(500)