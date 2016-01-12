Doorbell
========

A Raspberry Pi powered network doorbell server and client, with option for a Blinkstick powered RGB LED porch light.

My old standard doorbell ringer wasn't powerful enough to be heard throughout the house, so a doorbell with remote ringers was needed. Rather than using standard RF doorbells which may or may not reach the required distance, I decided to create a Pi powered doorbell and ringer that would work over the existing network, eliminating the need for further wires.

Clone the project:
	cd /home/pi/
	mkdir Projects
	cd Projects
	git clone git://github.com/worlds6440/Doorbell

Install Blickstick and Flask:
	sudo pip install blinkstick
	sudo pip install Flask

Configure Doorbell Server:
	Change project directory within doorbell.py
	Change SMTP details in Doorbell_server.py

	(Assuming the server pi also is a client)
	Change server IP within Doorbell_Client.py

Configure Doorbell Client:
	Change server IP within Doorbell_Client.py
	Change isServer to False in doorbell.py

To Test:
	sudo python doorbell.py
	(check server IP:5000 web address in a browser)

Ensure clock is always correct:
	sudo crontab -e
	(Add the following line to the end of the file(corrected for project directory of course))
	0 * * * * sh /home/pi/Projects/Doorbell/NTPUpdate.sh

Ensure all python files and shell scripts in project directory are executable
	cd /home/pi/Projects/Doorbell
	sudo chmod +x *.py
	sudo chmod +x *.sh

And finally, to run at boot:
	Ensure doorbell contains correct project install path.
	copy doorbell to /etc/init.d/
	sudo chmod +x /etc/init.d/doorbell
	sudo update-rc.d doorbell defaults
