#!/bin/bash
START=true
LINKS_CREATED=false

while $START; do
  readarray -t PIDS < <(exec pgrep -x fbi)
  
  # Check if source file exists and links haven't been created yet
  if [[ -f "/var/tmp/pwnagotchi/pwnagotchi.png" && "$LINKS_CREATED" == false ]]; then
    sudo ln -sf /var/tmp/pwnagotchi/pwnagotchi.png /var/tmp/pwnagotchi/pwnagotchi_1.png
    sudo ln -sf /var/tmp/pwnagotchi/pwnagotchi.png /var/tmp/pwnagotchi/pwnagotchi_2.png
    sudo ln -sf /var/tmp/pwnagotchi/pwnagotchi.png /var/tmp/pwnagotchi/pwnagotchi_3.png
    LINKS_CREATED=true
  fi

  # Only proceed if all three links exist
  if [[ -f "/var/tmp/pwnagotchi/pwnagotchi_1.png" && 
        -f "/var/tmp/pwnagotchi/pwnagotchi_2.png" && 
        -f "/var/tmp/pwnagotchi/pwnagotchi_3.png" ]]; then
    
    if [[ ${#PIDS[@]} -eq 0 ]]; then
      sudo fbi -T 1 /var/tmp/pwnagotchi/pwnagotchi_1.png \
                    /var/tmp/pwnagotchi/pwnagotchi_2.png \
                    /var/tmp/pwnagotchi/pwnagotchi_3.png \
                    -noverbose -t 1 -cachemem 0 -a
    elif ps -fp "${PIDS[@]}" | fgrep -F '<defunct>' >/dev/null; then
      sudo killall fbi
    fi
  fi
  
  sleep 5
done