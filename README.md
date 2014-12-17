Doorbell
========

A Raspberry Pi powered network doorbell server and client, with option for a Blinkstick powered RGB LED porch light.

My old standard doorbell ringer wasn't powerful enough to be heard throughout the house, so a doorbell with remote ringers was needed. Rather than using standard RF doorbells which may or may not reach the required distance, I decided to create a Pi powered doorbell and ringer that would work over the existing network, eliminating the need for further wires.

To install:
 - Clone the project:
 - cd /home/pi/
 - git clone git://github.com/worlds6440/Doorbell

 - Run sudo crontab -e and add the following line:
 - @reboot sh /home/pi/Doorbell/launcher_flask.sh >/home/pi/Doorbell/logs/cronlog 2>&1
