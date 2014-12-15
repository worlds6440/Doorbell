#!/bin/sh
# launcher.sh
# To run this file, edit the root crontab:
# sudo crontab -e
# and add the line:
# @reboot sh /home/pi/doorbell/launcher.sh >/home/pi/logs/cronlog 2>&1

cd /
cd home/pi/doorbell
sudo python flask_app &
cd /
