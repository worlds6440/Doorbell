import sys
import flask
import DoorBell_Client
import DoorBell_Server
import PorchLights
from blinkstick import blinkstick
import threading
import time
import socket
import subprocess
import os.path
from ConfigParser import SafeConfigParser

isServer = True

flask_app = flask.Flask("Flask_App")

# Door Bell Server
doorbell_s = None
if isServer:
	doorbell_s = DoorBell_Server.DoorBell_Server()
	# Kick off new thread listening for new sockets
	Thread_1 = threading.Thread(target=doorbell_s.SocketServer)
	Thread_1.start()
	# Kick off new thread listening for doorbell events
	Thread_2 = threading.Thread(target=doorbell_s.main)
	Thread_2.start()

# Door Bell Client
doorbell_c = DoorBell_Client.DoorBell_Client()
# Kick off new thread listening for doorbell events
Thread_3 = threading.Thread(target=doorbell_c.SocketClient)
Thread_3.start()

# Porch Lights
porchlight = None
if isServer:
	porchlight = PorchLights.PorchLights(r_led_count=5, max_rgb_value=255)
	porchlight.constructor()
	# Change the number of LEDs for r_led_count
	Thread_4 = threading.Thread(target=porchlight.run)
	Thread_4.start()

def WriteSettingsToFile():
	# Store all configuration options in a file
	global porchlight
	global doorbell_s
	global doorbell_c

	filename = "config.ini"

	# Get config file
	config = SafeConfigParser()
	# Only bother reading if file exists
	if os.path.isfile(filename):
		config.read(filename)

	selected_ding = ""
	selected_dong = ""
	if doorbell_c != None:
		selected_ding = doorbell_c.get_selected_ding()
		selected_dong = doorbell_c.get_selected_dong()

	# *** Client Settings ***
	try:
		config.add_section('client')
	except:
		print("")
	# Ding Sound File
	config.set('client', 'ding', selected_ding)
	# Dong Sound File
	config.set('client', 'dong', selected_dong)

	red = 0
	green = 0
	blue = 0
	if porchlight != None:
		red, green, blue = porchlight.get_led_colour()
	hex_colour = rgb_to_hex( (red, green, blue) )

	# *** Porchlight Settings ***
	try:
		config.add_section('porchlight')
	except:
		print("")
	# Light Colour
	config.set('porchlight', 'colour', hex_colour)
	# Light On Time
	#config.set('porchlight', 'time_on', 'value1')
	# Light Off Time
	#config.set('porchlight', 'time_off', 'value1')

	# Write new config options to file
	with open(filename, 'w') as f:
		config.write(f)
		f.close()
	return

def ReadSettingsFromFile():
	# Retrieve all configuration options from a file
	global porchlight
	global doorbell_s
	global doorbell_c

	filename = "config.ini"

	# Only bother reading if file exists
	if os.path.isfile(filename):
		# Get config file
		config = SafeConfigParser()
		config.read(filename)

		# *** Client Settings ***
		# Ding Sound File
		selected_ding = config.get('client', 'ding')
		# Dong Sound File
		selected_dong = config.get('client', 'dong')

		# *** Porchlight Settings ***
		# Light Colour
		hex_colour = config.get('porchlight', 'colour')
		# Light On Time
		#config.set('porchlight', 'time_on', 'value1')
		# Light Off Time
		#config.set('porchlight', 'time_off', 'value1')

		# Convert Hex colour to RGB values
		rgb_colour = hex_to_rgb( hex_colour )
		red = int(rgb_colour[0])
		green = int(rgb_colour[1])
		blue = int(rgb_colour[2])

		# Push new values back to Porch light thread
		if porchlight != None:
			porchlight.set_led_colour(red, green, blue)
		# Push new values back to Doorbell Client thread
		if doorbell_c != None:
			doorbell_c.set_selected_ding(selected_ding)
			doorbell_c.set_selected_dong(selected_dong)
	return

def hex_to_rgb(hex_str):
	# Simple method to convert hex colour to RGB
	hex_str = hex_str.lstrip('#')
	lv = len(hex_str)
	return tuple(int(hex_str[i:i + lv // 3], 16) for i in range(0, lv, lv // 3))

def rgb_to_hex(rgb):
	return '#%02x%02x%02x' % rgb

# manual call to reboot the doorbell
@flask_app.route("/reboot/", methods=["POST", "GET", "PUT"])
def reboot():
	if (flask.request.method == "POST" or flask.request.method == "PUT"):
		command = "/usr/bin/sudo /sbin/shutdown -r now"
		process = subprocess.Popen(command.split(), stdout=subprocess.PIPE)
		output = process.communicate()[0]
		print output
	return flask.render_template("rebooting.html")

# manual call to show the doorbell logs
@flask_app.route("/logs/", methods=["POST", "GET", "PUT"])
def logs():
	global doorbell_s

	# Debug, write the settings file here
	WriteSettingsToFile()

	logs = ["No Log Entries..."]
	if (flask.request.method == "POST" or flask.request.method == "PUT"):
		if doorbell_s:
			logs = doorbell_s.GetLogsFromFile()
		return flask.render_template("logs.html", doorbell_log=logs, submitted="Showing Doorbell Logs")

# manual call to ring the doorbell
@flask_app.route("/ring/", methods=["POST", "GET", "PUT"])
def dingdong():
	global porchlight
	global doorbell_s
	global doorbell_c

	red = 0
	green = 0
	blue = 0
	if porchlight != None:
		red, green, blue = porchlight.get_led_colour()

	hex_colour = rgb_to_hex( (red, green, blue) )

	# Get the list of sockets to display onto the website
	sockets = ["192.168.1.248"]
	wav_options = []
	selected_ding = ""
	selected_dong = ""
	if doorbell_s != None:
		sockets = doorbell_s.get_socket_list()
	if doorbell_c != None:
		wav_options = doorbell_c.get_wav_options()
		selected_ding = doorbell_c.get_selected_ding()
		selected_dong = doorbell_c.get_selected_dong()

	# POST or PUT -- Manually call a ding dong event
	if (flask.request.method == "POST" or flask.request.method == "PUT") and doorbell_s != None:
		doorbell_s.Ding()
		time.sleep(0.5)
		doorbell_s.Dong()
		return flask.render_template("index.html", hex_colour=hex_colour, socket_list=sockets, wav_options=wav_options, selected_ding=selected_ding, selected_dong=selected_dong, submitted="Ding-Dong called")
	else:
		return flask.render_template("index.html", hex_colour=hex_colour, socket_list=sockets, wav_options=wav_options, selected_ding=selected_ding, selected_dong=selected_dong)

# List all config options and allow user to edit them
@flask_app.route("/", methods=["POST", "GET", "PUT"])
def list():
	global porchlight
	global doorbell_s
	global doorbell_c

	red = 0
	green = 0
	blue = 0
	if porchlight != None:
		red, green, blue = porchlight.get_led_colour()

	hex_colour = rgb_to_hex( (red, green, blue) )
	
	# Get the list of sockets to display onto the website
	sockets = []
	wav_options = []
	selected_ding = ""
	selected_dong = ""
	if doorbell_s != None:
		sockets = doorbell_s.get_socket_list()

	if doorbell_c != None:
		wav_options = doorbell_c.get_wav_options()
		selected_ding = doorbell_c.get_selected_ding()
		selected_dong = doorbell_c.get_selected_dong()

	# POST or PUT -- set the LED Colour to the passed in value
	if flask.request.method == "POST" or flask.request.method == "PUT":
		# Pull values from HTML Form
		hex_colour = flask.request.form["colorhex"]
		# Convert Hex colour to RGB values
		rgb_colour = hex_to_rgb( hex_colour )
		red = int(rgb_colour[0])
		green = int(rgb_colour[1])
		blue = int(rgb_colour[2])
		# Doorbell Sounds
		selected_ding = flask.request.form["selected_ding"]
		selected_dong = flask.request.form["selected_dong"]
		
		# Push new values back to Porch light thread
		if porchlight != None:
			porchlight.set_led_colour(red, green, blue)
		# Push new values back to Doorbell Client thread
		if doorbell_c != None:
			doorbell_c.set_selected_ding(selected_ding)
			doorbell_c.set_selected_dong(selected_dong)
		# User has changed something, must update config file
		WriteSettingsToFile()
		# Show changes by refreshing webpage
		return flask.render_template("index.html", hex_colour=hex_colour, socket_list=sockets, wav_options=wav_options, selected_ding=selected_ding, selected_dong=selected_dong, submitted="Submitted")

	# GET -- return the list of config options
	elif flask.request.method == "GET":
		return flask.render_template("index.html", hex_colour=hex_colour, socket_list=sockets, wav_options=wav_options, selected_ding=selected_ding, selected_dong=selected_dong)


# Kick off the flask server
try:
	# Read configuration options from file
	ReadSettingsFromFile()
	# Run the flask app
	flask_app.run(host='0.0.0.0', debug=False)
except (KeyboardInterrupt, SystemExit):
	# Tell threads to quit
	if doorbell_s != None:
		doorbell_s.set_exit()
	if doorbell_c != None:
		doorbell_c.set_exit()
	if porchlight != None:
		porchlight.set_exit()
	# Then quit
	sys.exit(0)
