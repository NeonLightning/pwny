# to show or not show the number of passwords
# main.plugins.sorted-wpa-sec-list.show_number = True or False

import logging, json, os, glob, pwnagotchi
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
                color: white;
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
                    }else{
                        tr[i].style.display = "none";
                    }
                }
            }
        }
    }
{% endblock %}
{% block content %}
    <input type="text" id="searchText" placeholder="Search for ..." title="Type in a filter">
    <table id="tableOptions">
        <tr>
            <th>SSID</th>
            <th>BSSID</th>
            <th>Password</th>
        </tr>
        {% for p in passwords %}
            <tr>
                <td data-label="SSID">{{p["ssid"]}}</td>
                <td data-label="BSSID">{{p["bssid"]}}</td>
                <td data-label="Password">{{p["password"]}}</td>
            </tr>
        {% endfor %}
    </table>
{% endblock %}
"""


class WpaSecList(plugins.Plugin):
    __author__ = 'edited by neonlightning'
    __version__ = '1.1.1'
    __license__ = 'GPL3'
    __description__ = 'List cracked passwords from wpa-sec'

    def __init__(self):
        self.count = 0
        self.show_number = True

    def on_loaded(self):
        try:
            self.show_number = self.options.get('show_number', True)
        except Exception as e:
            logging.exception(f"[wpa-sec-list] error setting up: {e}")
        logging.info("[Wpa-sec-list] plugin loaded")

    def on_config_changed(self, config):
        self.config = config

    def _load_passwords(self):
        """Helper method to load and parse the cracked passwords file."""
        passwords = []
        try:
            if os.path.exists(os.path.join(self.config['bettercap']['handshakes'], 'wpa-sec.cracked.potfile')):
                with open(os.path.join(self.config['bettercap']['handshakes'], 'wpa-sec.cracked.potfile'), 'r') as file_in:
                    wpa_lines = [line.strip() for line in file_in.read().split() if line.strip()]
            else:
                logging.info("[Wpa-sec-list] no wpa-sec.cracked.potfile")
            if os.path.exists('/root/remote_cracking.potfile'):
                with open('/root/remote_cracking.potfile', 'r') as file_in:
                    rc_lines = [line.strip() for line in file_in.read().split() if line.strip()]
            else:
                logging.info("[Wpa-sec-list] no remote_cracking.potfile")
            if not os.path.exists(os.path.join(self.config['bettercap']['handshakes'], 'wpa-sec.cracked.potfile')) and not os.path.exists('/root/remote_cracking.potfile'):
                logging.info("[Wpa-sec-list] no potfiles found")
            unique_lines = set()
            for line in wpa_lines:
                fields = line.split(":")
                unique_lines.add((fields[0], fields[2], fields[3]))
            for line in rc_lines:
                fields = line.split(":")
                unique_lines.add((fields[1], fields[3], fields[4]))
            
            for line_tuple in sorted(unique_lines, key=lambda x: x[1]):
                password = {
                    "ssid": line_tuple[1],
                    "bssid": line_tuple[0],
                    "password": line_tuple[2]
                }
                passwords.append(password)
            return passwords
        except Exception as e:
            logging.error(f"[wpa-sec-list] error while loading passwords: {e}")
            logging.debug(e, exc_info=True)
            return []

    def on_webhook(self, path, request):
        if path == "/" or not path:
            passwords = self._load_passwords()
            return render_template_string(TEMPLATE,
                                          title="Passwords list",
                                          passwords=passwords)

    def on_ui_setup(self, ui):
        if self.show_number:
            try:
                ui.add_element("passwords", LabeledValue(color=BLACK, label="Passes:", value="0", position=(100, 93), label_font=fonts.Small, text_font=fonts.Small))
            except Exception as e:
                logging.error(f"[wpa-sec-list] error setting up ui: {e}")

    def on_ui_update(self, ui):
        if self.show_number:
            passwords = self._load_passwords()
            self.count = len(passwords)
            logging.debug(f"[wpa-sec-list] {self.count}")
            ui.set("passwords", str(self.count))
            self.count = 0

    def on_unload(self, ui):
        if self.show_number:
            with ui._lock:
                try:
                    ui.remove_element('passwords')
                except Exception as e:
                    logging.error(f"[wpa-sec-list] {e}")