# to show or not show the number of passwords
# main.plugins.sorted-Sorted-Password-List.show_number = True or False

import logging, os, json
from pwnagotchi.ui.components import LabeledValue
from pwnagotchi.ui.view import BLACK
import pwnagotchi.ui.fonts as fonts
import pwnagotchi.plugins as plugins
from flask import render_template_string

TEMPLATE = """
{% extends "base.html" %}
{% set active_page = "passwordsList" %}
{% block title %}
    {{ title }}
{% endblock %}
{% block meta %}
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, user-scalable=0" />
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
    function sortTable(columnIndex) {
        var table, rows, switching, i, x, y, shouldSwitch, dir, switchcount = 0;
        table = document.getElementById("tableOptions");
        switching = true;
        dir = "asc";
        while (switching) {
            switching = false;
            rows = table.rows;
            for (i = 1; i < (rows.length - 1); i++) {
                shouldSwitch = false;
                x = rows[i].getElementsByTagName("TD")[columnIndex];
                y = rows[i + 1].getElementsByTagName("TD")[columnIndex];
                if (dir == "asc") {
                    if (x.textContent.toLowerCase() > y.textContent.toLowerCase()) {
                        shouldSwitch = true;
                        break;
                    }
                } else if (dir == "desc") {
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
                if (switchcount == 0 && dir == "asc") {
                    dir = "desc";
                    switching = true;
                }
            }
        }
    }
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
            <th class="sortable">SSID</th>
            <th class="sortable">BSSID</th>
            <th class="sortable">Password</th>
            <th class="sortable">Origin</th>
            <th class="sortable">GPS</th>
        </tr>
        {% for p in passwords %}
            <tr>
                <td data-label="SSID">{{ p["ssid"] }}</td>
                <td data-label="BSSID">{{ p["bssid"] }}</td>
                <td data-label="Password">{{ p["password"] }}</td>
                <td data-label="Origin">{{ p["filename"] }}</td>
                <td data-label="GPS">
                    {% if p["lat"] and p["lng"] %}
                        <a href="{{ p["google_maps_link"] }}" target="_blank">{{ p["lat"] }}, {{ p["lng"] }}</a>
                    {% else %}
                        no gps.json found
                    {% endif %}
                </td>
            </tr>
        {% endfor %}
    </table>
{% endblock %}
"""

class SortedPasswordList(plugins.Plugin):
    __author__ = 'neonlightning'
    __version__ = '1.0.1'
    __license__ = 'GPL3'
    __description__ = 'List cracked passwords and show count of them.'

    def __init__(self):
        self.count = 0
        self.show_number = True

    def on_loaded(self, config):
        self.config = config
        try:
            self.show_number = self.options.get('show_number', True)
        except Exception as e:
            logging.exception(f"[Sorted-Password-List] error setting up: {e}")
        logging.info("[Sorted-Password-List] plugin loaded")

    def on_config_changed(self, config):
        self.config = config
        
    def _load_passwords(self, with_location=False):
        passwords = []
        try:
            lineswpa = []
            linesrc = []
            if os.path.exists(os.path.join(self.config['bettercap']['handshakes'], 'wpa-sec.cracked.potfile')):
                logging.debug("[Sorted-Password-List] loading wpa-sec.cracked.potfile")
                with open(os.path.join(self.config['bettercap']['handshakes'], 'wpa-sec.cracked.potfile'), 'r') as file_in:
                    lineswpa = [(line.strip(), 'wpa-sec.cracked.potfile') for line in file_in.readlines() if line.strip()]
            if os.path.exists('/root/remote_cracking.potfile'):
                logging.debug("[Sorted-Password-List] loading remote_cracking.potfile")
                with open('/root/remote_cracking.potfile', 'r') as file_in:
                    linesrc = [(line.strip(), 'remote_cracking.potfile') for line in file_in.readlines() if line.strip()]
            if not lineswpa and not linesrc:
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
                        "google_maps_link": None
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
                        "google_maps_link": None
                    })
            return sorted(passwords, key=lambda x: x["ssid"])
        except Exception as err:
            logging.exception(f"[Sorted-Password-List] error while loading passwords: {repr(err)}")
            return []
        
    def _get_location_info(self, ssid, bssid):
        ssid = ssid.replace(" ", "")
        geojson_file = (f"/root/handshakes/{ssid}_{bssid}.gps.json")
        if os.path.exists(geojson_file):
            with open(geojson_file, 'r') as geo_file:
                data = json.load(geo_file)
            if data is not None:
                lat = data.get('Latitude') or data.get('location', {}).get('lat')
                lng = data.get('Longitude') or data.get('location', {}).get('lng')
                if lat is not None and lng is not None:
                    google_maps_link = f"https://www.google.com/maps?q={lat},{lng}"
                    return lat, lng, google_maps_link
        return None, None, None
    
    def on_webhook(self, path, request):
        if path == "/" or not path:
            passwords = self._load_passwords(with_location=False)
            for p in passwords:
                lat, lng, google_maps_link = self._get_location_info(p['ssid'], p['bssid'])
                p["lat"] = lat
                p["lng"] = lng
                p["google_maps_link"] = google_maps_link
            return render_template_string(TEMPLATE,
                                        title="Passwords list",
                                        passwords=passwords)

    def on_ui_setup(self, ui):
        if self.show_number:
            try:
                passwords = self._load_passwords()
                self.count = len(passwords)
                ui.add_element("passwords", LabeledValue(color=BLACK, label="Passes:", value=self.count, position=(100, 93), label_font=fonts.Small, text_font=fonts.Small))
            except Exception as e:
                logging.error(f"[Sorted-Password-List] error setting up ui: {e}")

    def on_ui_update(self, ui):
        if self.show_number:
            passwords = self._load_passwords()
            self.count = len(passwords)
            logging.debug(f"[Sorted-Password-List] {self.count}")
            ui.set("passwords", str(self.count))
            self.count = 0

    def on_unload(self, ui):
        if self.show_number:
            with ui._lock:
                try:
                    ui.remove_element('passwords')
                except Exception as e:
                    logging.error(f"[Sorted-Password-List] {e}")
        logging.info(f"[Sorted-Password-List] unloaded")