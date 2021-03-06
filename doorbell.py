#!/usr/bin/env python
import sys
import flask
import DoorBell_Client
import DoorBell_Server
import PorchLights
import threading
import time
import subprocess
import os.path
from ConfigParser import SafeConfigParser

# Version number
version = 2.0

# Class pointers
doorbell_c = None
doorbell_s = None
porchlight = None
isServer = True
# List of text values user can type in that mean "yes"
yes_list = ['true', '1', 't', 'y', 'yes', 'yeah', 'yup', 'certainly', 'uh-huh']

# Project installation directory
project_dir = "/home/pi/Projects/Doorbell/"
if len(sys.argv) > 1:
    project_dir = sys.argv[1]
# Ensure project path ends in trailing '/'
os.path.join(project_dir, '')


def GetServerFlagFromFile():
    # Retrieve Server flag from file
    global isServer
    filename = "server.ini"

    # Only bother reading if file exists
    if os.path.isfile(filename):
        # Get config file
        config = SafeConfigParser()
        config.read(filename)

        # *** Server Settings ***
        # Is Server flag (the one connected to doorbell and porchlight)
        isServer = False
        strisServer = config.get('server', 'isserver')
        if strisServer in yes_list:
            isServer = True
    return


def WriteServerFlagToFile():
    # Store Server flag to file
    global isServer
    filename = "server.ini"

    # Get config file
    config = SafeConfigParser()
    # Only bother reading if file exists
    if os.path.isfile(filename):
        config.read(filename)

    # *** Server Settings ***
    try:
        config.add_section('server')
    except:
        print("")
    # Is Server flag (the one connected to doorbell
    if isServer:
        config.set('server', 'isserver', '1')
    else:
        config.set('server', 'isserver', '0')
    return


# Change to Doorbell folder
os.chdir(project_dir)
flask_app = flask.Flask("Flask_App")

# Get the server flag from config file
GetServerFlagFromFile()

# Door Bell Server
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
if isServer:
    porchlight = PorchLights.PorchLights()
    # No longer need to call this as using actual constructor
    #porchlight.constructor()
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

    # *** Client Settings ***
    selected_ding = ""
    selected_dong = ""
    if doorbell_c is not None:
        selected_ding = doorbell_c.get_selected_ding()
        selected_dong = doorbell_c.get_selected_dong()
    try:
        config.add_section('client')
    except:
        print("")
    # Ding Sound File
    config.set('client', 'ding', selected_ding)
    # Dong Sound File
    config.set('client', 'dong', selected_dong)

    # *** Porchlight Settings ***
    red = 0
    green = 0
    blue = 0
    if porchlight is not None:
        red, green, blue = porchlight.get_led_colour(0)
    hex_colour = rgb_to_hex((red, green, blue))
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
        rgb_colour = hex_to_rgb(hex_colour)
        red = int(rgb_colour[0])
        green = int(rgb_colour[1])
        blue = int(rgb_colour[2])

        # Push new values back to Porch light thread
        if porchlight is not None:
            porchlight.set_all_led_colour(red, green, blue)
        # Push new values back to Doorbell Client thread
        if doorbell_c is not None:
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
        print(output)
    return flask.render_template("rebooting.html")


# manual call to ring the doorbell
@flask_app.route("/ring/", methods=["POST", "GET", "PUT"])
def dingdong():
    global porchlight
    global doorbell_s
    global doorbell_c

    red = 0
    green = 0
    blue = 0
    if porchlight is not None:
        red, green, blue = porchlight.get_led_colour(0)

    hex_colour = rgb_to_hex((red, green, blue))

    # Get the list of sockets to display onto the website
    sockets = ["192.168.1.248"]
    wav_options = []
    selected_ding = ""
    selected_dong = ""
    if doorbell_s is not None:
        sockets = doorbell_s.get_socket_list()
    if doorbell_c is not None:
        wav_options = doorbell_c.get_wav_options()
        selected_ding = doorbell_c.get_selected_ding()
        selected_dong = doorbell_c.get_selected_dong()

    # POST or PUT -- Manually call a ding dong event
    if (
        (
            flask.request.method == "POST"
            or flask.request.method == "PUT"
        )
        and (doorbell_s is not None)
    ):
        doorbell_s.Ding()
        time.sleep(0.5)
        doorbell_s.Dong()
        return flask.render_template(
            "index.html",
            hex_colour=hex_colour,
            socket_list=sockets,
            wav_options=wav_options,
            selected_ding=selected_ding,
            selected_dong=selected_dong,
            submitted="Ding-Dong called"
        )
    else:
        return flask.render_template(
            "index.html",
            hex_colour=hex_colour,
            socket_list=sockets,
            wav_options=wav_options,
            elected_ding=selected_ding,
            selected_dong=selected_dong
        )


# List all config options and allow user to edit them
@flask_app.route("/", methods=["POST", "GET", "PUT"])
def list():
    global porchlight
    global doorbell_s
    global doorbell_c
    global isServer

    red = 0
    green = 0
    blue = 0
    if porchlight is not None:
        red, green, blue = porchlight.get_led_colour(0)

    # Get the list of sockets to display onto the website
    sockets = []
    wav_options = []
    selected_ding = ""
    selected_dong = ""
    logs = ["No Log Entries..."]
    isEmail = False
    if doorbell_s is not None:
        sockets = doorbell_s.get_socket_list()
        logs = doorbell_s.GetLogsFromFile()
        isEmail = doorbell_s.is_email()

    if doorbell_c is not None:
        wav_options = doorbell_c.get_wav_options()
        selected_ding = doorbell_c.get_selected_ding()
        selected_dong = doorbell_c.get_selected_dong()

    # POST or PUT -- set the LED Colour to the passed in value
    if flask.request.method == "POST" or flask.request.method == "PUT":
        # Pull values from HTML Form
        strred = flask.request.form['RDisp']
        strgreen = flask.request.form['GDisp']
        strblue = flask.request.form['BDisp']
        red = int(strred)
        green = int(strgreen)
        blue = int(strblue)
        # Doorbell Sounds
        selected_ding = flask.request.form.get("selected_ding", None)
        selected_dong = flask.request.form.get("selected_dong", None)
        # Push Email flag to main app
        isEmail = False
        strisemail = flask.request.form.get("isemail", None)
        if strisemail in yes_list:
            isEmail = True
        # Push new values back to doorbell server thread
        if doorbell_s is not None:
            doorbell_s.set_email(isEmail)
        # Push new values back to Porch light thread
        if porchlight is not None:
            porchlight.set_all_led_colour(red, green, blue)
        # Push new values back to Doorbell Client thread
        if doorbell_c is not None:
            doorbell_c.set_selected_ding(selected_ding)
            doorbell_c.set_selected_dong(selected_dong)
        # Push Server flag to main app
        isServer = False
        strisServer = flask.request.form.get("isserver", None)
        if strisServer in yes_list:
            isServer = True
        # User has changed something, must update config file
        WriteSettingsToFile()
        WriteServerFlagToFile()

    # Ensure sockets list is a list, not None
    if sockets is None:
        sockets = []
    # Ensure wave options list is a list, not None
    if wav_options is None:
        wav_options = []

    # Show changes by refreshing webpage
    # upgraded to split out RGB into three colours
    return flask.render_template(
        "index.html",
        RDisp=red,
        GDisp=green,
        BDisp=blue,
        doorbell_log=logs,
        socket_list=sockets,
        wav_options=wav_options,
        selected_ding=selected_ding,
        selected_dong=selected_dong,
        isserver=isServer,
        isemail=isEmail
    )

# Kick off the flask server
try:
    # Read configuration options from file
    ReadSettingsFromFile()
    # Run the flask app
    flask_app.run(host='0.0.0.0', debug=False)
except (KeyboardInterrupt, SystemExit):
    # Tell threads to quit
    if doorbell_s is not None:
        doorbell_s.set_exit()
    if doorbell_c is not None:
        doorbell_c.set_exit()
    if porchlight is not None:
        porchlight.set_exit()
    # Then quit
    sys.exit(0)
