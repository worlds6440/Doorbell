#!/usr/bin/env python
import sys
import threading
import RPi.GPIO as GPIO
import time
# import socket
import smtplib
import socketserver
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText
from email.MIMEBase import MIMEBase
from email import encoders
from email.utils import COMMASPACE, formatdate
import logging
import subprocess
import os
import time

class DoorBell_Server:
    def __init__(self):
        # Member variables
        self.DEBUG = False
        logging.basicConfig(filename='/home/pi/Projects/Doorbell/email.log',level=logging.DEBUG)

        # SMTP login details
        self.send_email = True
        self.LOGIN = "worlds6440@gmail.com"
        self.PASSWORD = "obib00th"
        self.FROMADDR = "worlds6440@gmail.com"
        self.TOADDRS = ["worlds6440@gmail.com"]
        self.SUBJECT = "Doorbell Pressed"
        self.SMTP_SERVER = "smtp.gmail.com"
        # TEXT = "The doorbell was just pressed."

        # Socket Stuff
        self.s_server = None
        self.BUFF = 1024
        self.HOST = ''
        self.PORT = 9999

        self.pin_button = 23
        self.pin_led = 24
        # time we last sent an email notification
        self.time_email = 0
        # Min time in seconds between email notifications
        self.time_email_gap = 30.0
        self.time_pressed_last = time.time()
        self.time_released_last = time.time()
        # time gap in seconds
        self.time_gap = 1.0

        # List of dings and dongs
        self.playing = []
        self.limit_number = 4
        # max time allowed for holding button
        self.time_held_limit = 1
        self.isPressed = False
        self.veto_release = False

        # flag set when we want the process to exit
        self.exit = False

    def stop(self):
        """ Inform everything to close now. """
        self.exit = True
        if self.s_server is not None:
            self.s_server.stop()

    def set_email(self, send_email):
        """ Set email variable. """
        self.send_email = send_email

    def is_email(self):
        """ Return email variable. """
        return self.send_email

    def SocketServer(self):
        """ Start listening for sockets.
        NOTE: This method will block forever. """
        self.s_server = socketserver.SocketServer(
            BUFF=self.BUFF,
            HOST=self.HOST,
            PORT=self.PORT
        )
        self.s_server.start()

    def SendToSockets(self, message):
        """ Send DING/DONG to all sockets
        Grab the lock to the list of sockets. """
        if self.s_server:
            self.s_server.SendToSockets(message)

    def SendEmail(self):
        """ Attempt to send an email notification
        Note that the TO variable must be a list, and that you have
        to add the From, To, and Subject headers to the message yourself. """
        if self.send_email:

            #os.system('ssh pi@192.168.1.105 "python /home/pi/Projects/clear_folders/make_video.py"')
            #if not os.path.exists('/home/pi/Projects/Doorbell/pi/Projects/clear_folders/'):
            #    os.system('sshfs  pi@192.168.1.105: /home/pi/Projects/Doorbell/pi/')
            #os.system('mv /home/pi/Projects/Doorbell/pi/Projects/clear_folders/*.mp4 /home/pi/Projects/Doorbell/')
            #os.system('sudo umount /home/pi/Projects/Doorbell/pi/')

            try:
                logging.debug('Making remote video')
                returned_value = subprocess.call('ssh -i /home/pi/.ssh/id_rsa pi@192.168.1.105 "python /home/pi/Projects/clear_folders/make_video.py"', shell=True)
                logging.debug(returned_value)
                if not os.path.exists('/home/pi/Projects/Doorbell/pi/Projects/clear_folders/'):
                    logging.debug('Mounting SSHFS Directory')
                    returned_value = subprocess.call('sshfs -o IdentityFile=/home/pi/.ssh/id_rsa pi@192.168.1.105: /home/pi/Projects/Doorbell/pi/', shell=True)
                    logging.debug(returned_value)
                logging.debug('Moving remote file to local system')
                returned_value = subprocess.call('mv /home/pi/Projects/Doorbell/pi/Projects/clear_folders/*.mp4 /home/pi/Projects/Doorbell/', shell=True)
                logging.debug(returned_value)
                logging.debug('Unmounting SSHFS')
                returned_value = subprocess.call('sudo umount /home/pi/Projects/Doorbell/pi/', shell=True)
                logging.debug(returned_value)
            except Exception as e:
                logging.debug(e)

            filename_list = []
            for file in os.listdir("/home/pi/Projects/Doorbell/"):
                if file.endswith(".mp4"):
                    filename_list.append(os.path.join("/home/pi/Projects/Doorbell", file))

            logging.debug('Making Message')
            try:
                # Message body
                localtime = time.asctime(time.localtime(time.time()))
                text = "Doorbell pressed (" + localtime + ")\r\n"

                # Prepare message headers
                msg = MIMEMultipart()
                msg['From'] = self.FROMADDR
                msg['To'] = ", ".join(self.TOADDRS)
                msg['Date'] = formatdate(localtime=True)
                msg['Subject'] = self.SUBJECT
                msg.attach(MIMEText(text))
                #msg = (
                #    "From: %s\r\nTo: %s\r\nSubject: %s\r\n\r\n"
                #    % (self.FROMADDR, ", ".join(self.TOADDRS), self.SUBJECT)
                #)

                # Attach file
                if len(filename_list):
                    logging.debug('Attaching File')
                    path, filename = os.path.split(filename_list[0])
                    attachment = open(filename_list[0], "rb")

                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload((attachment).read())
                    encoders.encode_base64(part)
                    part.add_header('Content-Disposition', "attachment; filename= %s" % filename)
                    msg.attach(part)

                logging.debug('Attempting to send email')
                # Send the mail
                try:
                    server = smtplib.SMTP(self.SMTP_SERVER, 587)
                    server.set_debuglevel(0)  # Debug output == 1
                    server.ehlo()
                    server.starttls()
                    server.login(self.LOGIN, self.PASSWORD)
                    server.sendmail(self.FROMADDR, self.TOADDRS, msg.as_string())
                    server.quit()
                    if self.DEBUG:
                        print("Successfully sent email")
                except (KeyboardInterrupt, SystemExit):
                    logging.debug('Error sending email')
                    if self.DEBUG:
                        print("Error: unable to send email")

                # Delete mp4 files
                for file in filename_list:
                    os.remove(file)
            except Exception as e:
                logging.debug(e)

    def Ding(self):
        # Thin out audio playing list
        self.processPlaying(self.playing, self.limit_number)
        # Send DING to all sockets
        self.SendToSockets("DING\n")
        # Turn LED ON and play sound
        GPIO.output(self.pin_led, True)

    def Dong(self):
        # Thin out audio playing list
        self.processPlaying(self.playing, self.limit_number)
        # Send DING to all sockets
        self.SendToSockets("DONG\n")
        # Turn LED OFF and play sound
        GPIO.output(self.pin_led, False)

    def tick(self):
        """ Called every second to perform clearup tasks. """
        if (self.DEBUG):
            print("Tick called")

        # Calculate time since last clicked
        time_now = time.time()
        time_pressed_diff = time_now - self.time_pressed_last
        time_released_diff = time_now - self.time_released_last

        # Check to see if currently pressed AND pressed over a set time ago
        pin_value = GPIO.input(self.pin_button)
        if (
            time_pressed_diff < time_released_diff and
            time_pressed_diff >= self.time_held_limit and
            pin_value
        ):
            # Veto next release
            self.buttonReleased(0)
            self.veto_release = True

        # Sanitise the playing list
        self.processPlaying(self.playing, self.limit_number)

    def processPlaying(self, playing, limit_number):
        """ Remove finished processes and limit processes to a set number. """
        if (self.DEBUG):
            print("Process Playing called")

        count = len(playing)
        if (count >= limit_number):
            # Remove the first few until process count is low enough
            for n in range(0, (count - limit_number)):
                item = playing[0]
                if item.poll() is None:
                    item.terminate()  # Wasnt finished, make it finished
                playing.pop(0)  # remove first item from list

    def button(self, channel):
        """ Button has been either pressed or released
        Its a rising or falling edge, check pin value to see which. """
        pin_value = GPIO.input(self.pin_button)
        if (pin_value):
            self.buttonPressed(channel)
        else:
            self.buttonReleased(channel)

    def buttonPressed(self, channel):
        time_now = time.time()
        time_diff = time_now - self.time_pressed_last
        if (time_diff >= self.time_gap):
            # Time since previous press is longer than min gap
            if (self.DEBUG):
                print("Button pressed!")

            self.isPressed = True
            self.AppendDateToFile()
            self.Ding()

            # Send Email Notification in new thread
            time_now = time.time()
            time_diff = time_now - self.time_email
            if time_diff >= self.time_email_gap:
                # Only send email if time since last
                # email is longer than set gap
                self.time_email = time_now
                t_email = threading.Thread(target=self.SendEmail)
                t_email.start()

            # Remember last successful button press
            self.time_pressed_last = time_now

    def buttonReleased(self, channel):
        if (self.DEBUG):
            print("Release called")

        time_now = time.time()
        time_diff = time_now - self.time_released_last
        if (
            time_diff >= self.time_gap and
            not self.veto_release and
            self.isPressed
        ):
            # Time since previous press is longer than min gap
            if (self.DEBUG):
                print("Button released!")
            self.isPressed = False
            self.Dong()
            # Remember last successful button press
            self.time_released_last = time_now
        # Reset variable
        self.veto_release = False

    def AppendDateToFile(self):
        """ Append to file (will create if didnt already exist). """
        filename = "doorbell.txt"
        with open(filename, "a+") as myfile:
            localtime = time.asctime(time.localtime(time.time()))
            myfile.write("Doorbell " + localtime + "\n")
            myfile.close()

    def GetLogsFromFile(self):
        # Read the log file and return the list of entries
        filename = "doorbell.txt"
        logs = ["No Entires"]

        try:
            with open(filename, "r") as myfile:
                logs = [x.strip('\n') for x in myfile.readlines()]
                myfile.close()
        except:
            pass

        # Log is returned in ascending date.
        # We want it reversed
        if logs is not None and len(logs):
            logs.reverse()
        return logs

    def main(self):
        if (self.DEBUG):
            print("Started")
        try:
            # set up GPIO using BCM numbering
            GPIO.setmode(GPIO.BCM)

            # Set GPIO pins appropriately
            if (self.DEBUG):
                print("GPIO Button and LED Setup")
            GPIO.setup(
                self.pin_button,
                GPIO.IN,
                pull_up_down=GPIO.PUD_DOWN
            )
            GPIO.setup(
                self.pin_led,
                GPIO.OUT
            )
            if (self.DEBUG):
                print("GPIO Event Callback Setup")
            GPIO.add_event_detect(
                self.pin_button,
                GPIO.BOTH,
                callback=self.button
            )
            if (self.DEBUG):
                print("Init LED to OFF")
            GPIO.output(self.pin_led, False)
            self.GPIOCleaned = False

            if (self.DEBUG):
                print("Waiting for Button Press")

            # Loop infinitely waiting for button presses
            loopCount = 0
            while not self.exit:
                # Perform a sound cleanup every second.
                self.tick()

                # Sleep for 1 second intervals
                time.sleep(1)
                loopCount += 1
        except:
            # Get here if we press Ctrl+C or GPIO failure
            e = sys.exc_info()[0]
            print("Error: %s" % e)
            self.GPIOCleaned = True
            GPIO.cleanup()
            if (self.DEBUG):
                print("Cleanup-exception")

        # Get here if we exit script neatly
        if (not self.GPIOCleaned):
            GPIO.cleanup()
            if (self.DEBUG):
                print("Cleanup-normal")

    def get_socket_list(self):
        """ Return a list of string host names
        that are connected to this doorbell. """
        socket_list = []
        try:
            if self.s_server:
                socket_list = self.s_server.get_socket_list()
        except:
            pass
        return socket_list
