# to show or not show the number of passwords
# all configs are optional
################################################################
# this will show the number of unique passwords
# main.plugins.sorted-password-list.show_number = True or False
# this will keep the qr files in /pi/home/qrcodes/ when you create one
# main.plugins.sorted-password-list.keep_qr = True or False
# this will limit the fields displayed in webui to the ones chosen
# main.plugins.sorted-password-list.fields = ['ssid', 'bssid', 'password', 'origin', 'gps', 'strength']
# this will set a custom position (X, Y)
# main.plugins.sorted-password-list.position = "0,93"
# you can display a qr code for each password
# main.plugins.sorted-password-list.qr_display = True or False
# you will need to sudo apt install python3-qrcode

import logging, os, json, re, pwnagotchi, tempfile, socket, time, math
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
    function parseDistance(distanceStr) {
        if (distanceStr === "Unknown") return Infinity;
        var parts = distanceStr.split(" ");
        var num = parseFloat(parts[0]);
        if (parts[1] === "km") return num * 1000;
        return num;
    }
    function parseStrength(strengthStr) {
        const num = parseInt(strengthStr);
        return isNaN(num) ? -9999 : num;
    }
    var currentSortColumn = -1;
    var currentSortDirection = 'asc';
    function applyDefaultSort() {
        const table = document.getElementById("tableOptions");
        const headers = table.getElementsByTagName("th");
        let strengthCol = -1, distanceCol = -1, ssidCol = -1;
        for (let i = 0; i < headers.length; i++) {
            const header = headers[i].textContent.trim().replace(' ↑', '').replace(' ↓', '');
            if (header === "Strength") strengthCol = i;
            else if (header === "Distance") distanceCol = i;
            else if (header === "SSID") ssidCol = i;
        }
        if (strengthCol !== -1 || distanceCol !== -1 || ssidCol !== -1) {
            const rows = Array.from(table.rows).slice(1);
            rows.sort((a, b) => {
                if (strengthCol !== -1) {
                    const aStrength = parseStrength(a.cells[strengthCol].textContent.trim());
                    const bStrength = parseStrength(b.cells[strengthCol].textContent.trim());
                    if (aStrength !== bStrength) return bStrength - aStrength;
                }
                if (distanceCol !== -1) {
                    const aDist = parseDistance(a.cells[distanceCol].textContent.trim());
                    const bDist = parseDistance(b.cells[distanceCol].textContent.trim());
                    if (aDist !== bDist) return aDist - bDist;
                }
                if (ssidCol !== -1) {
                    const aSSID = a.cells[ssidCol].textContent.trim();
                    const bSSID = b.cells[ssidCol].textContent.trim();
                    return aSSID.localeCompare(bSSID, undefined, { numeric: true });
                }
                return 0;
            });
            while (table.rows.length > 1) table.deleteRow(1);
            rows.forEach(row => table.appendChild(row));
        }
    }
    function sortTable(columnIndex) {
        const table = document.getElementById("tableOptions");
        const headers = table.getElementsByTagName("th");
        const rows = Array.from(table.rows).slice(1);
        if (columnIndex === currentSortColumn) {
            currentSortDirection = currentSortDirection === 'asc' ? 'desc' : 'asc';
        } else {
            currentSortColumn = columnIndex;
            currentSortDirection = 'asc';
        }
        for (let i = 0; i < headers.length; i++) {
            headers[i].innerHTML = headers[i].innerHTML.replace(' ↑', '').replace(' ↓', '');
        }
        const indicator = currentSortDirection === 'asc' ? ' ↑' : ' ↓';
        headers[columnIndex].innerHTML += indicator;
        const dataType = headers[columnIndex].getAttribute('data-type');
        let parser;
        if (dataType === 'distance') parser = parseDistance;
        else if (dataType === 'strength') parser = parseStrength;
        else parser = val => val;
        rows.sort((a, b) => {
            const aVal = parser(a.cells[columnIndex].textContent.trim());
            const bVal = parser(b.cells[columnIndex].textContent.trim());
            let comparison = 0;
            if (typeof aVal === 'number' && typeof bVal === 'number') {
                comparison = aVal - bVal;
            } else {
                comparison = String(aVal).localeCompare(String(bVal), undefined, {numeric: true});
            }
            return currentSortDirection === 'asc' ? comparison : -comparison;
        });
        while (table.rows.length > 1) table.deleteRow(1);
        rows.forEach(row => table.appendChild(row));
    }
    window.onload = function() {
        applyDefaultSort();
        document.querySelectorAll("th.sortable").forEach((th, index) => {
            th.addEventListener("click", () => sortTable(index));
        });
    };
{% endblock %}
{% block content %}
    <input type="text" id="searchText" placeholder="Search for ..." title="Type in a filter">
    <table id="tableOptions">
        <tr>
            {% if ssid_display %}
                <th class="sortable" data-type="string">SSID</th>
            {% endif %}
            {% if bssid_display %}
                <th class="sortable" data-type="string">BSSID</th>
            {% endif %}
            {% if password_display %}
                <th class="sortable" data-type="string">Password</th>
            {% endif %}
            {% if origin_display %}
                <th class="sortable" data-type="string">Origin</th>
            {% endif %}
            {% if distance_display %}
                <th class="sortable" data-type="distance">Distance</th>
            {% endif %}
            {% if gps_display %}
                <th class="sortable" data-type="string">GPS</th>
            {% endif %}
            {% if strength_display %}
                <th class="sortable" data-type="strength">Strength</th>
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
                {% if distance_display %}
                    <td data-label="Distance">
                        {% if p["distance"] %}
                            {{ p["distance"] }}
                        {% else %}
                            Unknown
                        {% endif %}
                    </td>
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
    __version__ = '2.0.9'
    __license__ = 'GPL3'
    __description__ = 'List cracked passwords and show count of them.'

    def __init__(self):
        self.counter = 3
        self.count = 0
        self.show_number = True
        self.qr_display = False
        self.fields = ['ssid', 'bssid', 'password', 'origin', 'distance', 'gps', 'strength']
        self.sorted_aps = []
        self.rssi_data = {}
        self._agent = None
        self.keep_qr = False
        self.trackgps = False
        self.gps_socket = None
        self.last_gps_fix = (0, 0)
        self.gps_last_update = 0
        self.last_update = time.time()
        self.last_gps_update = 0
        self.curr_gps_lat = 0
        self.curr_gps_lon = 0
        self.last_gps = (0, 0)

    def on_ready(self, agent):
        self._agent = agent
        if self.distance_display: 
            self._update_gps_and_distances()
        logging.info("[Sorted-Password-List] plugin loaded")

    def on_loaded(self):
        try:
            import qrcode
            qr_library_available = True
        except ImportError:
            qr_library_available = False
        try:
            self.fields = self.options.get('fields', ['ssid', 'bssid', 'password', 'origin', 'distance', 'gps', 'strength'])
            self.show_number = self.options.get('show_number', True)
            self.keep_qr = self.options.get('keep_qr', False)
            self.ssid_display = 'ssid' in self.fields
            self.bssid_display = 'bssid' in self.fields
            self.password_display = 'password' in self.fields
            self.origin_display = 'origin' in self.fields
            self.distance_display = 'distance' in self.fields
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
            linespwc = []
            if os.path.exists('/home/pi/handshakes/cracked.pwncrack.potfile'):
                with open('/home/pi/handshakes/cracked.pwncrack.potfile', 'r') as file_in:
                    linespwc = [(line.strip(), 'cracked.pwncrack.potfile') for line in file_in.readlines() if line.strip()]
            else:
                pass
            if os.path.exists('/home/pi/handshakes/wpa-sec.cracked.potfile'):
                with open('/home/pi/handshakes/wpa-sec.cracked.potfile', 'r') as file_in:
                    lineswpa = [(line.strip(), 'wpa-sec.cracked.potfile') for line in file_in.readlines() if line.strip()]
            else:
                pass
            if os.path.exists('/home/pi/handshakes/remote_cracking.potfile'):
                with open('/home/pi/handshakes/remote_cracking.potfile', 'r') as file_in:
                    linesrc = [(line.strip(), 'remote_cracking.potfile') for line in file_in.readlines() if line.strip()]
            else:
                pass
            if not lineswpa and not linesrc and not linespwc:
                logging.info("[Sorted-Password-List] no potfiles found")
                return []
            unique_lines = set()
            for line, filename in linespwc:
                fields = line.split(":")
                entry = (fields[1], fields[3], fields[4])
                if entry not in unique_lines:
                    unique_lines.add(entry)
                    passwords.append({
                        "ssid": entry[1],
                        "bssid": entry[0],
                        "password": entry[2],
                        "filename": filename,
                        "distance": None,
                        "lat": None,
                        "lng": None,
                        "google_maps_link": None,
                        "rssi": None
                    })
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
                        "distance": None,
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
                        "distance": None,
                        "lat": None,
                        "lng": None,
                        "google_maps_link": None,
                        "rssi": None
                    })
            return sorted(passwords, key=lambda x: x["ssid"])
        except Exception as err:
            logging.exception(f"[Sorted-Password-List] error while loading passwords: {repr(err)}")
            return []

    def _current_gps(self):
        try:
            if self.gps_socket is None:
                self.gps_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.gps_socket.settimeout(5.0)
                try:
                    self.gps_socket.connect(('localhost', 2947))
                    self.gps_socket.sendall(b'?WATCH={"enable":true,"json":true}\n')
                    time.sleep(0.5)
                except (ConnectionRefusedError, socket.timeout) as e:
                    logging.debug(f"[Sorted-Password-List] GPSd connection failed: {e}")
                    self.gps_socket = None
                    return 0, 0
            self.gps_socket.settimeout(1.0)
            try:
                data = self.gps_socket.recv(4096).decode('utf-8')
                if not data:
                    raise ConnectionResetError("Empty response from GPSd")
                for line in data.splitlines():
                    try:
                        report = json.loads(line)
                        if report.get('class') == 'TPV':
                            lat = report.get('lat')
                            lon = report.get('lon')
                            if lat is not None and lon is not None:
                                self.last_gps_fix = (lat, lon)
                                self.gps_last_update = time.time()
                                return lat, lon
                    except (json.JSONDecodeError, KeyError):
                        continue
                if time.time() - self.gps_last_update < 30:
                    return self.last_gps_fix
                return 0, 0
            except (socket.timeout, ConnectionResetError, BrokenPipeError) as e:
                logging.debug(f"[Sorted-Password-List] GPS read error: {e}")
                self.gps_socket = None
                if time.time() - self.gps_last_update < 30:
                    return self.last_gps_fix
                return 0, 0
        except Exception as e:
            logging.exception(f"[Sorted-Password-List] Unexpected GPS error: {e}")
            self.gps_socket = None
            return 0, 0

    def _update_gps_and_distances(self):
        current_gps = self._current_gps()
        if current_gps != (0, 0):
            self.curr_gps_lat, self.curr_gps_lon = current_gps
            self.last_gps = current_gps
            self.last_gps_update = time.time()
            self.trackgps = True
        passwords = self._load_passwords()
        for p in passwords:
            if self.distance_display:
                lat, lng, google_maps_link, distance = self._get_location_info(p['ssid'], p['bssid'])
                p["lat"] = lat
                p["lng"] = lng
                p["google_maps_link"] = google_maps_link
                p["distance"] = distance or "Unknown"

    def _get_location_info(self, ssid, bssid):
        ssid = re.sub(r'\W+', '', ssid)
        geojson_file = (f"/home/pi/handshakes/{ssid}_{bssid}.gps.json")
        distance = None
        if os.path.exists(geojson_file):
            with open(geojson_file, 'r') as geo_file:
                data = json.load(geo_file)
            if data is not None:
                lat = data.get('Latitude') or data.get('location', {}).get('lat')
                lng = data.get('Longitude') or data.get('location', {}).get('lng')
                if lat is not None and lng is not None:
                    google_maps_link = f"https://www.google.com/maps?q={lat},{lng}"
                    if self.curr_gps_lat != 0 and self.curr_gps_lon != 0:
                        lat1 = math.radians(self.curr_gps_lat)
                        lon1 = math.radians(self.curr_gps_lon)
                        lat2 = math.radians(lat)
                        lon2 = math.radians(lng)
                        dlon = lon2 - lon1
                        dlat = lat2 - lat1
                        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
                        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
                        distance = 6371000 * c
                        if distance >= 1000:
                            distance = f"{distance/1000:.2f} km"
                        else:
                            distance = f"{distance:.0f} m"
                    return lat, lng, google_maps_link, distance
        return None, None, None, None

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
                        folder_path = os.path.dirname(png_filepath)
                        if not os.path.exists(folder_path):
                            os.makedirs(folder_path)
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
                    lat, lng, google_maps_link, distance = self._get_location_info(p['ssid'], p['bssid'])
                    p["lat"] = lat
                    p["lng"] = lng
                    p["google_maps_link"] = google_maps_link
                if self.distance_display:
                    p["distance"] = distance or "Unknown"
                if self.strength_display:
                    p["rssi"] = self.rssi_data.get(p['bssid'], 'Not Nearby')
            return render_template_string(TEMPLATE,
                                          title="Passwords list",
                                          passwords=passwords,
                                          qr_display=self.qr_display,
                                          ssid_display=self.ssid_display,
                                          bssid_display=self.bssid_display,
                                          password_display=self.password_display,
                                          origin_display=self.origin_display,
                                          distance_display=self.distance_display,
                                          gps_display=self.gps_display,
                                          strength_display=self.strength_display
                                          )

    def on_ui_setup(self, ui):
        logging.info("[Sorted-Password-List] Initial GPS update successful")
        current_gps = self._current_gps()
        if current_gps != (0, 0):
            self.curr_gps_lat, self.curr_gps_lon = current_gps
            self.last_gps = current_gps
            self.trackgps = True
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
        current_time = time.time()
        if current_time - self.last_update > 300:
            logging.info("[Sorted-Password-List] Updating GPS")
            current_gps = self._current_gps()
            if current_gps != (0, 0):
                self.curr_gps_lat, self.curr_gps_lon = current_gps
                self.last_gps = current_gps
                self.last_gps_update = current_time
                self.trackgps = True
            else:
                if hasattr(self, 'last_gps') and (current_time - self.last_gps_update) <= 1800:
                    self.curr_gps_lat, self.curr_gps_lon = self.last_gps
                else:
                    self.curr_gps_lat, self.curr_gps_lon = 0, 0
                    self.trackgps = False
            self.last_update = current_time
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
        if self.gps_socket:
            try:
                self.gps_socket.close()
            except:
                pass
            self.gps_socket = None
        logging.info(f"[Sorted-Password-List] unloaded")