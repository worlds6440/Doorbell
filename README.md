# Doorbell
========

A Raspberry Pi powered network doorbell server and client, with option for a Blinkstick powered RGB LED porch light.

My old standard doorbell ringer wasn*t powerful enough to be heard throughout the house, so a doorbell with remote ringers was needed. Rather than using standard RF doorbells which may or may not reach the required distance, I decided to create a Pi powered doorbell and ringer that would work over the existing network, eliminating the need for further wires.

## Clone the project:
	cd /home/pi/
	mkdir Projects
	cd Projects
	git clone git://github.com/worlds6440/Doorbell

## Install Blinkstick and Flask:
	sudo pip install blinkstick
	sudo pip install Flask

## Configure Doorbell Server:
Edit *doorbell.py* and change project directory if you have put the project in a different location.  
Edit *Doorbell_server.py* and change SMTP details.  

(Assuming the server pi also is a client)
Edit *Doorbell_Client.py* and change server IP.  

## Configure Doorbell Client:
Edit *Doorbell_Client.py* and change server IP.  
Edit *doorbell.py* and change isServer to False.  

## To Test:
	sudo python doorbell.py
To check server is up and running, got to *http://IP:5000* in a web browser.  

## Ensure clock is always correct:
	sudo crontab -e
Add the following line to the end of the file(corrected for project directory of course).  
	0 * * * * sh /home/pi/Projects/Doorbell/NTPUpdate.sh

## Ensure all python files and shell scripts in project directory are executable
	cd /home/pi/Projects/Doorbell
	sudo chmod +x *.py
	sudo chmod +x *.sh

## And finally, to run at boot:
Ensure *doorbell* init.d script file contains correct project install path.  
	sudo cp /home/pi/Projects/Doobell/doorbell /etc/init.d/
	sudo chmod +x /etc/init.d/doorbell
	sudo update-rc.d doorbell defaults
