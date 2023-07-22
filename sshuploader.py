from fileinput import filename
from genericpath import isfile
from operator import truediv
from datetime import datetime
import pwnagotchi, logging, os, subprocess
import pwnagotchi.plugins as plugins

class SSHUploader(plugins.Plugin):
    __author__ = 'NeonLightning'
    __version__ = '0.0.1'
    __license__ = 'GPL3'
    __description__ = 'uploads hashes over ssh'

    def __init__(self):
        self.ssh_host = '10.0.0.1'
        self.ssh_port = 22
        self.ssh_username = ''
        self.ssh_password = ''
        self.remote_directory = 'd:\\pwnagotchi\\handshakes'
        self.local_directory = '/root/handshakes'
        self.tracking_file = '/root/.shakes'

    def on_loaded(self):
        logging.info("[SSHUploader] loaded")
        self.loaded = True

    def on_unloaded(self):
        logging.info("[SSHUploader] unloaded")
        self.loaded = False
        return

    def on_internet_available(self, agent):
        if self.handshake_found:
            self.check_files_changed()
            self.handshake_found = False

    def on_handshake(self, agent, filename, access_point, client_station):
        result = subprocess.run(f'/usr/bin/aircrack-ng {filename} | grep "1 handshake" | awk \'{{print $2}}\'',
                                shell=True, capture_output=True, text=True)
        if result.stdout.strip():
            self.handshake_found = True
            logging.info("[SSHUpload] Found handshake in " + filename)
        else:
            result = subprocess.run(f'/usr/bin/aircrack-ng {filename} | grep "PMKID" | awk \'{{print $2}}\'',
                                    shell=True, capture_output=True, text=True)
            os.remove(filename)

    def check_files_changed(self):
        try:
            uploaded_files = {}
            if os.path.exists(self.tracking_file):
                with open(self.tracking_file, 'r') as file:
                    for line in file:
                        file_name, file_mtime = line.strip().split(':')
                        uploaded_files[file_name] = float(file_mtime)
            changed_files = []
            for file_name in os.listdir(self.local_directory):
                file_path = os.path.join(self.local_directory, file_name)
                if os.path.isfile(file_path):
                    local_mtime = os.path.getmtime(file_path)
                    if file_name not in uploaded_files or local_mtime > uploaded_files[file_name]:
                        changed_files.append(file_path)
            if changed_files:
                self.upload_files(changed_files)
        except Exception as e:
            logging.error(f"[SSHUploader] Error checking files: {str(e)}")

    def upload_files(self, file_paths):
        try:
            for file_path in file_paths:
                file_name = os.path.basename(file_path)
                remote_file = os.path.join(self.remote_directory, file_name)
                remote_mtime = self.get_remote_file_mtime(remote_file)
                if remote_mtime is None or os.path.getmtime(file_path) > remote_mtime:
                    try:
                        subprocess.run(['sshpass', '-p', self.ssh_password, 'scp', '-P', str(self.ssh_port), file_path,
                                        f'{self.ssh_username}@{self.ssh_host}:{self.remote_directory}'],
                                        check=True)
                    except Exception as e:
                        logging.error("[SSHUploader] error sending " + file_path + ": " + str(e))
                    continue
            if os.path.isfile(self.tracking_file):
                with open(self.tracking_file, 'a') as file:
                    for file_path in file_paths:
                        file_name = os.path.basename(file_path)
                        file_mtime = os.path.getmtime(file_path)
                        file.write(f"{file_name}:{file_mtime}\n")
            else:
                with open(self.tracking_file, 'w') as file:
                    for file_path in file_paths:
                        file_name = os.path.basename(file_path)
                        file_mtime = os.path.getmtime(file_path)
                        file.write(f"{file_name}:{file_mtime}\n")
        except Exception as e:
            logging.error("[SSHUploader] error uploading files: " + str(e))
            
    def get_remote_file_mtime(self, remote_file):
        try:
            ssh_command_exists = ['sshpass', '-p', self.ssh_password, 'ssh', '-o', 'StrictHostKeyChecking=accept-new', '-p', str(self.ssh_port),
                                f'{self.ssh_username}@{self.ssh_host}', f'test -e {remote_file} && echo 1 || echo 0']
            exists_output = subprocess.check_output(ssh_command_exists)
            remote_file_exists = bool(int(exists_output.strip()))
            if remote_file_exists:
                ssh_command_mtime = ['sshpass', '-p', self.ssh_password, 'ssh', '-o', 'StrictHostKeyChecking=accept-new', '-p', str(self.ssh_port),
                                    f'{self.ssh_username}@{self.ssh_host}', f'stat -c %Y {remote_file}']
                output = subprocess.check_output(ssh_command_mtime)
                return float(output.strip())
            else:
                return 0.0
        except subprocess.CalledProcessError as e:
            logging.error(f"[SSHUploader] Error getting remote file modification time: {str(e)}")
            return None