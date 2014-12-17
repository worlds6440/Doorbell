#!/bin/sh
# launcher.sh
# To run this file, edit the root crontab:
# sudo crontab -e
# and add the line:
# @reboot sh /home/pi/Doorbell/launcher.sh >/home/pi/Doorbell/logs/cronlog 2>&1

cd /
cd home/pi/Doorbell
sudo python flask_app &
cd /
