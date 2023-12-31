import pwnagotchi.plugins as plugins

import logging
import subprocess
import string
import os

'''
Aircrack-ng needed, to install:
> apt-get install aircrack-ng
'''


class AircrackOnly(plugins.Plugin):
    __author__ = 'pwnagotchi [at] rossmarks [dot] uk'
    __version__ = '1.0.1'
    __license__ = 'GPL3'
    __description__ = 'confirm pcap contains handshake/PMKID or delete it'

    def on_loaded(self):
        logging.info("aircrackonly plugin loaded")
        check = subprocess.run(
            ('/usr/bin/dpkg -l aircrack-ng | grep aircrack-ng | awk \'{print $2, $3}\''), shell=True, stdout=subprocess.PIPE)
        check = check.stdout.decode('utf-8').strip()
        if check != "aircrack-ng <none>":
            logging.info("aircrackonly: Found " + check)
        else:
            logging.warning("aircrack-ng is not installed!")

    def on_handshake(self, agent, filename, access_point, client_station):
        todelete = 0
        handshakeFound = 0

        result = subprocess.run(('/usr/bin/aircrack-ng ' + filename + ' | grep "1 handshake" | awk \'{print $2}\''),
                                shell=True, stdout=subprocess.PIPE)
        result = result.stdout.decode('utf-8').translate({ord(c): None for c in string.whitespace})
        if result:
            handshakeFound = 1
            logging.info("[AircrackOnly] contains handshake")

        if handshakeFound == 0:
            result = subprocess.run(('/usr/bin/aircrack-ng ' + filename + ' | grep "PMKID" | awk \'{print $2}\''),
                                    shell=True, stdout=subprocess.PIPE)
            result = result.stdout.decode('utf-8').translate({ord(c): None for c in string.whitespace})
            if result:
                logging.info("[AircrackOnly] contains PMKID")
            else:
                todelete = 1

        if todelete == 1:
            os.remove(filename)
            logging.warning("Removed uncrackable pcap " + filename)
