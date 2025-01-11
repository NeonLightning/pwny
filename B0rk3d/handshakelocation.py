# goto ipinfo.io to get the api_key
# main.plugins.handshakelocationplugin.api_key = "api_key"
import logging
import pwnagotchi
import os
import json
import requests
import pwnagotchi.plugins as plugins
from datetime import datetime

class HandshakeLocationPlugin(plugins.Plugin):
    __author__ = "NeonLightning"
    __version__ = "1.0.1"
    __license__ = 'GPL3'
    __description__ = 'netgps.'

    def __init__(self):
        try:
            logging.info("[HandshakeLocationPlugin] Initializing HandshakeLocationPlugin...")
            self.handshake_dir = "/root/handshakes"
            self.loc_save_time_file = "/root/.locsavetime"
            self.ready = False
            logging.info("[HandshakeLocationPlugin] Initialized HandshakeLocationPlugin")
        except Exception as e:
            logging.exception(f"[HandshakeLocationPlugin] failed to initialize: {e}")

    def _get_last_save_time(self):
        if os.path.exists(self.loc_save_time_file):
            with open(self.loc_save_time_file, 'r') as f:
                return f.read().strip()
        return None

    def _update_last_save_time(self, timestamp):
        try:
            with open(self.loc_save_time_file, 'w') as f:
                f.write(timestamp)
            logging.info(f"[HandshakeLocationPlugin] Updated last save time to {timestamp}")
        except Exception as e:
            logging.error(f"[HandshakeLocationPlugin] Error updating last save time: {e}")

    def on_loaded(self):
        try:
            self.api_key = self.options.get('api_key', "NOT FOUND")
            self.api_url = f"https://ipinfo.io/json?token={self.api_key}"
            logging.debug(f"[HandshakeLocationPlugin] initialized with IPinfo token: {self.api_key}")
            self.ready = True
            logging.info("[HandshakeLocationPlugin] ready")
        except Exception as e:
            logging.exception(f"[HandshakeLocationPlugin] failed to set ready state: {e}")

    def on_handshake(self, agent, filename, access_point, client_station):
        if self.ready:
            logging.debug(f"[HandshakeLocationPlugin] access point: {access_point}")
            ssid = access_point.get('hostname')
            ssid = ssid.replace(' ', '')
            bssid = access_point.get('mac')
            bssid = bssid.replace(':', '')
            if not ssid or not bssid:
                logging.error("[HandshakeLocationPlugin] Missing SSID or BSSID in access point data.")
                return
            timestamp = datetime.now().isoformat()
            geo_json_file = os.path.join(self.handshake_dir, f"{ssid}_{bssid}.geo.json")
            try:
                handshake_data = {
                    "ts": timestamp
                }
                with open(geo_json_file, 'w') as f:
                    json.dump(handshake_data, f)
                logging.info(f"[HandshakeLocationPlugin] Stored handshake ts for {ssid} in {geo_json_file}")
            except Exception as e:
                logging.error(f"[HandshakeLocationPlugin] Error storing handshake ts: {e}")

    def on_internet_available(self, agent):
        if self.ready:
            try:
                last_save_time = self._get_last_save_time()
                current_time = datetime.now().isoformat()
                new_handshakes = False
                for filename in os.listdir(self.handshake_dir):
                    if filename.endswith(".geo.json"):
                        geo_json_file = os.path.join(self.handshake_dir, filename)
                        with open(geo_json_file, 'r') as f:
                            handshake_data = json.load(f)
                            ts = handshake_data.get('ts')
                            if ts and (last_save_time is None or ts > last_save_time):
                                new_handshakes = True
                                ssid_bssid = filename[:-9]
                                gps_json_file = os.path.join(self.handshake_dir, f"{ssid_bssid}.gps.json")
                                self._fetch_and_store_location(gps_json_file)
                if new_handshakes:
                    logging.info(f"[HandshakeLocationPlugin] updating to {current_time}")
                    self._update_last_save_time(current_time)
            except Exception as e:
                logging.error(f"[HandshakeLocationPlugin] Error during location check: {e}")

    def _fetch_and_store_location(self, gps_json_file):
        try:
            response = requests.get(self.api_url)
            if response.status_code == 200:
                json_response = response.json()
                loc = json_response.get('loc', '0,0')
                latitude, longitude = map(float, loc.split(','))
                location_info = {
                    "Longitude": longitude,
                    "Latitude": latitude
                }
                with open(gps_json_file, 'w') as f:
                    json.dump(location_info, f)
                logging.info(f"[HandshakeLocationPlugin] Updated location info in {gps_json_file}")
            else:
                logging.error(f"[HandshakeLocationPlugin] Failed to fetch location info. Status code: {response.status_code}")
        except Exception as e:
            logging.error(f"[HandshakeLocationPlugin] Error fetching location info: {e}")

    def on_unload(self, agent):
        self.ready = False
        logging.info("[HandshakeLocationPlugin] Plugin unloaded and marked as not ready.")
