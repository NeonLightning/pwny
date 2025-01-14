# to show or not show the number of passwords
# all configs are optional
################################################################
# this will show the number of unique passwords
# main.plugins.sorted-password-list.show_number = True or False
# this will keep the qr files in /root/handshakes/ when you create one
# main.plugins.sorted-password-list.keep_qr = True or False
# this will limit the fields displayed in webui to the ones chosen
# main.plugins.sorted-password-list.fields = ['ssid', 'bssid', 'password', 'origin', 'gps', 'strength']
# this will set a custom position (X, Y)
# main.plugins.sorted-password-list.position = "0,93"
# you can display a qr code for each password
# main.plugins.sorted-password-list.qr_display = True or False
# you will need to sudo apt install python3-qrcode

import logging, os, json, re, pwnagotchi, tempfile
from pwnagotchi.ui.components import LabeledValue
from pwnagotchi.ui.view import BLACK
import pwnagotchi.ui.fonts as fonts
import pwnagotchi.plugins as plugins
from pwnagotchi.bettercap import Client
from flask import render_template_string, send_file

TEMPLATE = """
{% extends "base.html" %}
{% set active_page = "passwordsList" %}
{% block title %}
    {{ title }}
{% endblock %}
{% block meta %}
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, user-scalable=0" />
    <meta name="csrf-token" content="{{ csrf_token() }}">
{% endblock %}
{% block styles %}
{{ super() }}
    <style>
        #searchText {
            width: 100%;
        }
        table {
            table-layout: auto;
            width: 100%;
        }
        table, th, td {
            border: 1px solid;
            border-collapse: collapse;
        }
        th, td {
            padding: 15px;
            text-align: left;
        }
        th.sortable {
            cursor: pointer;
        }
        th.sortable:hover {
            background-color: #f1f1f1;
        }
        @media screen and (max-width:700px) {
            table, tr, td {
                padding:0;
                border:1px solid;
            }
            table {
                border:none;
            }
            tr:first-child, thead, th {
                display:none;
                border:none;
            }
            tr {
                float: left;
                width: 100%;
                margin-bottom: 2em;
            }
            td {
                float: left;
                width: 100%;
                padding:1em;
            }
            td::before {
                content:attr(data-label);
                word-wrap: break-word;
                border-right:2px solid;
                width: 20%;
                float:left;
                padding:1em;
                font-weight: bold;
                margin:-1em 1em -1em -1em;
            }
        }
    </style>
{% endblock %}
{% block script %}
    function handlePasswordClick(password, ssid, bssid) {
        alert("One Moment");
        const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
        fetch('/plugins/sorted-password-list', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify({ password: password, ssid: ssid, bssid: bssid })
        })
        .then(response => {
            if (response.ok && response.headers.get("Content-Type").includes("image/png")) {
                return response.blob();
            } else {
                return response.json();
            }
        })
        .then(data => {
            if (data instanceof Blob) {
                const imgURL = URL.createObjectURL(data);
                window.open(imgURL, '_blank');
            } else if (data.message) {
                alert(data.message);
            }
        })
        .catch(error => console.error('Error:', error));
    }
    var searchInput = document.getElementById("searchText");
    searchInput.onkeyup = function() {
        var filter, table, tr, td, i, txtValue;
        filter = searchInput.value.toUpperCase();
        table = document.getElementById("tableOptions");
        if (table) {
            tr = table.getElementsByTagName("tr");
            for (i = 0; i < tr.length; i++) {
                td = tr[i].getElementsByTagName("td")[0];
                if (td) {
                    txtValue = td.textContent || td.innerText;
                    if (txtValue.toUpperCase().indexOf(filter) > -1) {
                        tr[i].style.display = "";
                    } else {
                        tr[i].style.display = "none";
                    }
                }
            }
        }
    }
    function sortTable(columnIndex, defaultDirection = 'asc') {
        var table, rows, switching, i, x, y, shouldSwitch, dir, switchcount = 0;
        table = document.getElementById("tableOptions");
        switching = true;
        dir = defaultDirection;
        while (switching) {
            switching = false;
            rows = table.rows;
            for (i = 1; i < (rows.length - 1); i++) {
                shouldSwitch = false;
                x = rows[i].getElementsByTagName("TD")[columnIndex];
                y = rows[i + 1].getElementsByTagName("TD")[columnIndex];

                if (dir === "asc") {
                    if (x.textContent.toLowerCase() > y.textContent.toLowerCase()) {
                        shouldSwitch = true;
                        break;
                    }
                } else if (dir === "desc") {
                    if (x.textContent.toLowerCase() < y.textContent.toLowerCase()) {
                        shouldSwitch = true;
                        break;
                    }
                }
            }
            if (shouldSwitch) {
                rows[i].parentNode.insertBefore(rows[i + 1], rows[i]);
                switching = true;
                switchcount++;
            } else {
                if (switchcount === 0 && dir === "asc") {
                    dir = "desc";
                    switching = true;
                }
            }
        }
    }
    function defaultSort() {
        var rssiColumnIndex = 5;
        var ssidColumnIndex = 0;
        var table = document.getElementById("tableOptions");
        var hasRSSI = Array.from(table.getElementsByTagName("tr")).some(function(row) {
            return row.getElementsByTagName("td")[rssiColumnIndex] && row.getElementsByTagName("td")[rssiColumnIndex].textContent.trim() !== "not nearby";
        });
        sortTable(hasRSSI ? rssiColumnIndex : ssidColumnIndex);
    }
    window.onload = defaultSort;
    document.querySelectorAll("th.sortable").forEach(function(th, index) {
        th.addEventListener("click", function() {
            sortTable(index);
        });
    });
{% endblock %}
{% block content %}
    <input type="text" id="searchText" placeholder="Search for ..." title="Type in a filter">
    <table id="tableOptions">
        <tr>
            {% if ssid_display %}
                <th class="sortable">SSID</th>
            {% endif %}
            {% if bssid_display %}
                <th class="sortable">BSSID</th>
            {% endif %}
            {% if password_display %}
                <th class="sortable">Password</th>
            {% endif %}
            {% if origin_display %}
                <th class="sortable">Origin</th>
            {% endif %}
            {% if gps_display %}
                <th class="sortable">GPS</th>
            {% endif %}
            {% if strength_display %}
                <th class="sortable">Strength</th>
            {% endif %}
        </tr>
        {% for p in passwords %}
            <tr>
                {% if ssid_display %}
                    <td data-label="SSID">{{ p["ssid"] }}</td>
                {% endif %}
                {% if bssid_display %}
                    <td data-label="BSSID">{{ p["bssid"] }}</td>
                {% endif %}
                {% if password_display %}
                    <td data-label="Password">
                        {% if qr_display %}
                            <a href="#" onclick="handlePasswordClick('{{ p['password'] }}', '{{ p['ssid'] }}', '{{ p['bssid'] }}')">
                                {{ p["password"] }}
                            </a>
                        {% else %}
                            {{ p["password"] }}
                        {% endif %}
                    </td>
                {% endif %}
                {% if origin_display %}
                    <td data-label="Origin">{{ p["filename"] }}</td>
                {% endif %}
                {% if gps_display %}
                    <td data-label="GPS">
                        {% if p["lat"] and p["lng"] %}
                            <a href="{{ p["google_maps_link"] }}" target="_blank">{{ p["lat"] }}, {{ p["lng"] }}</a>
                        {% else %}
                            no gps.json found
                        {% endif %}
                    </td>
                {% endif %}
                {% if strength_display %}
                    <td data-label="Strength">
                        {% if p["rssi"] %}
                            {{ p["rssi"] }}
                        {% else %}
                            not nearby
                        {% endif %}
                    </td>
                {% endif %}
            </tr>
        {% endfor %}
    </table>
{% endblock %}
"""


class SortedPasswordList(plugins.Plugin):
    __author__ = 'neonlightning'
    __version__ = '2.0.7'
    __license__ = 'GPL3'
    __description__ = 'List cracked passwords and show count of them.'

    def __init__(self):
        self.counter = 3
        self.count = 0
        self.show_number = True
        self.qr_display = False
        self.fields = ['ssid', 'bssid', 'password', 'origin', 'gps', 'strength']
        self.sorted_aps = []
        self.rssi_data = {}
        self._agent = None
        self.keep_qr = False

    def on_ready(self, agent):
        self._agent = agent
        logging.info("[Sorted-Password-List] plugin loaded")

    def on_loaded(self):
        try:
            import qrcode
            qr_library_available = True
        except ImportError:
            qr_library_available = False
        try:
            self.fields = self.options.get('fields', ['ssid', 'bssid', 'password', 'origin', 'gps', 'strength'])
            self.show_number = self.options.get('show_number', True)
            self.keep_qr = self.options.get('keep_qr', False)
            self.ssid_display = 'ssid' in self.fields
            self.bssid_display = 'bssid' in self.fields
            self.password_display = 'password' in self.fields
            self.origin_display = 'origin' in self.fields
            self.gps_display = 'gps' in self.fields
            self.strength_display = 'strength' in self.fields
            if qr_library_available:
                self.qr_display = self.options.get('qr_display', False)
            else:
                self.qr_display = False
            logging.info(f'[Sorted-Password-List] qr_display is {self.qr_display}')
        except Exception as e:
            logging.exception(f"[Sorted-Password-List] error setting up: {e}")

    def _load_passwords(self, with_location=False):
        passwords = []
        try:
            lineswpa = []
            linesrc = []
            lineswpa2 = []
            linesrc2 = []
            if os.path.exists('/home/pi/handshakes/wpa-sec.cracked.potfile'):
                with open('/home/pi/handshakes/wpa-sec.cracked.potfile', 'r') as file_in:
                    lineswpa = [(line.strip(), 'wpa-sec.cracked.potfile') for line in file_in.readlines() if line.strip()]
            if os.path.exists('/home/pi/handshakes/wpa-sec.cracked.potfile'):
                with open('/home/pi/handshakes/wpa-sec.cracked.potfile', 'r') as file_in:
                    lineswpa = [(line.strip(), 'wpa-sec.cracked.potfile') for line in file_in.readlines() if line.strip()]
            if os.path.exists('/home/pi/handshakes/wpa-sec.cracked.potfile'):
                with open('/root/handshakes/wpa-sec.cracked.potfile', 'r') as file_in:
                    lineswpa2 = [(line.strip(), 'wpa-sec.cracked.potfile') for line in file_in.readlines() if line.strip()]
            if os.path.exists('/home/pi/handshakes/remote_cracking.potfile'):
                with open('/home/pi/handshakes/remote_cracking.potfile', 'r') as file_in:
                    linesrc = [(line.strip(), 'remote_cracking.potfile') for line in file_in.readlines() if line.strip()]
            if os.path.exists('/root/handshakes/remote_cracking.potfile'):
                with open('/root/handshakes/remote_cracking.potfile', 'r') as file_in:
                    linesrc2 = [(line.strip(), 'remote_cracking.potfile') for line in file_in.readlines() if line.strip()]
            if not lineswpa and not linesrc and not lineswpa2 and not linesrc2:
                logging.info("[Sorted-Password-List] no potfiles found")
                return []
            unique_lines = set()
            for line, filename in lineswpa:
                fields = line.split(":")
                entry = (fields[0], fields[2], fields[3])
                if entry not in unique_lines:
                    unique_lines.add(entry)
                    passwords.append({
                        "ssid": entry[1],
                        "bssid": entry[0],
                        "password": entry[2],
                        "filename": filename,
                        "lat": None,
                        "lng": None,
                        "google_maps_link": None,
                        "rssi": None
                    })
            for line, filename in linesrc:
                fields = line.split(":")
                entry = (fields[1], fields[3], fields[4])
                if entry not in unique_lines:
                    unique_lines.add(entry)
                    passwords.append({
                        "ssid": entry[1],
                        "bssid": entry[0],
                        "password": entry[2],
                        "filename": filename,
                        "lat": None,
                        "lng": None,
                        "google_maps_link": None,
                        "rssi": None
                    })
            return sorted(passwords, key=lambda x: x["ssid"])
        except Exception as err:
            logging.exception(f"[Sorted-Password-List] error while loading passwords: {repr(err)}")
            return []

    def _get_location_info(self, ssid, bssid):
        ssid = re.sub(r'\W+', '', ssid)
        geojson_file = (f"/home/pi/handshakes/{ssid}_{bssid}.gps.json")
        geojson_file2 = (f"/root/handshakes/{ssid}_{bssid}.gps.json")
        if os.path.exists(geojson_file):
            with open(geojson_file, 'r') as geo_file:
                data = json.load(geo_file)
            if data is not None:
                lat = data.get('Latitude') or data.get('location', {}).get('lat')
                lng = data.get('Longitude') or data.get('location', {}).get('lng')
                if lat is not None and lng is not None:
                    google_maps_link = f"https://www.google.com/maps?q={lat},{lng}"
                    return lat, lng, google_maps_link
        elif os.path.exists(geojson_file2):
            with open(geojson_file, 'r') as geo_file:
                data = json.load(geo_file)
            if data is not None:
                lat = data.get('Latitude') or data.get('location', {}).get('lat')
                lng = data.get('Longitude') or data.get('location', {}).get('lng')
                if lat is not None and lng is not None:
                    google_maps_link = f"https://www.google.com/maps?q={lat},{lng}"
                    return lat, lng, google_maps_link
        return None, None, None

    def _get_rssi(self):
        try:
            if self._agent:
                wifi_info = self._agent.session(sess="session/wifi")
                aps = wifi_info.get('aps', [])
                if aps:
                    for ap in aps:
                        rssi = ap.get('rssi')
                        ssid = ap.get('hostname')
                        bssid = ap.get('mac')
                        bssid = bssid.replace(':', '')
                        if ssid != "<hidden>":
                            self.rssi_data[bssid] = rssi
        except Exception as e:
            logging.error(f"[Sorted-Password-List] Exception encountered: {e}")

    def on_webhook(self, path, request):
        if self.qr_display:
            import qrcode
            if request.method == "POST":
                try:
                    try:
                        data = request.json
                        password = data.get('password')
                        ssid = data.get('ssid')
                        bssid = data.get('bssid')
                        png_filepath = f'/home/pi/qrcodes/{ssid}_{bssid}_{password}.png'
                        if self.keep_qr:
                            if os.path.exists(png_filepath):
                                response = send_file(png_filepath, mimetype='image/png')
                            else:
                                qr_data = f"WIFI:T:WPA;S:{ssid};P:{password};;"
                                qr_code = qrcode.QRCode(
                                    error_correction=qrcode.constants.ERROR_CORRECT_L,
                                    box_size=10,
                                    border=4,
                                )
                                qr_code.add_data(qr_data)
                                qr_code.make(fit=True)
                                img = qr_code.make_image(fill_color="yellow", back_color="black")
                                img.save(png_filepath)
                                response = send_file(png_filepath, mimetype='image/png')
                        else:
                            with tempfile.NamedTemporaryFile(delete=False, suffix='.png', prefix='WIFIQR') as temp_file:
                                png_filepath = temp_file.name
                                qr_data = f"WIFI:T:WPA;S:{ssid};P:{password};;"
                                qr_code = qrcode.QRCode(
                                    error_correction=qrcode.constants.ERROR_CORRECT_L,
                                    box_size=10,
                                    border=4,
                                )
                                qr_code.add_data(qr_data)
                                qr_code.make(fit=True)
                                img = qr_code.make_image(fill_color="yellow", back_color="black")
                                img.save(png_filepath)
                                response = send_file(png_filepath, mimetype='image/png')
                        return response
                    finally:
                        if not self.keep_qr:
                            if os.path.exists(png_filepath):
                                os.remove(png_filepath)
                except Exception as e:
                    logging.error(f"[Sorted-Password-List] Error processing password click: {e}")
                    return json.dumps({"status": "error", "message": str(e)}), 500
        if path == "/" or not path:
            if self.strength_display:
                self._get_rssi()
            passwords = self._load_passwords(with_location=False)
            for p in passwords:
                if self.gps_display:
                    lat, lng, google_maps_link = self._get_location_info(p['ssid'], p['bssid'])
                    p["lat"] = lat
                    p["lng"] = lng
                    p["google_maps_link"] = google_maps_link
                    p["rssi"] = self.rssi_data.get(p['bssid'], 'Not Nearby')
            return render_template_string(TEMPLATE,
                                          title="Passwords list",
                                          passwords=passwords,
                                          qr_display=self.qr_display,
                                          ssid_display=self.ssid_display,
                                          bssid_display=self.bssid_display,
                                          password_display=self.password_display,
                                          origin_display=self.origin_display,
                                          gps_display=self.gps_display,
                                          strength_display=self.strength_display
                                          )

    def on_ui_setup(self, ui):
        self.counter = 0
        if self.show_number:
            pos = None
            if "position" in self.options:
                try:
                    pos = [int(x.strip()) for x in self.options["position"].split(",")]
                    if not len(pos) >= 2:
                        logging.error("[Sorted-Password-List] Could not process set position, using default.")
                    elif len(pos) > 2:
                        logging.error("[Sorted-Password-List] Too many positions set (only two are needed: x,y), using the first two.")
                        pos = (pos[0], pos[1])
                    else:
                        pos = (pos[0], pos[1])
                except Exception:
                    logging.error("[Sorted-Password-List] Could not process set position, using default.")

            if not pos:
                pos = (0, 98)

            ui.add_element("passwords", LabeledValue(color=BLACK, label="Passes:", value="...", position=pos, label_font=fonts.Small, text_font=fonts.Small))

    def on_ui_update(self, ui):
        if self.counter >= 3:
            if self.show_number:
                passwords = self._load_passwords()
                self.count = len(passwords)
                ui.set("passwords", str(self.count))
            self.counter = 0
        self.counter += 1

    def on_unload(self, ui):
        if self.show_number:
            with ui._lock:
                try:
                    ui.remove_element('passwords')
                except Exception as e:
                    logging.error(f"[Sorted-Password-List] {e}")
        logging.info(f"[Sorted-Password-List] unloaded")
