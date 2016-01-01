#!/usr/bin/env python
import sys
import threading
import RPi.GPIO as GPIO
import time
import socket
import smtplib


class DoorBell_Server:
    def __init__(self):
        # Constructor

        # Member variables
        self.SOCKET_DEBUG = True
        self.DEBUG = False
        self.serversock = None
        self.serversock = None
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
        # List of open connections
        self.socketList = []
        self.lock = threading.Lock()
        self.BUFF = 1024
        # '127.0.0.1'# must be input parameter @TODO
        self.HOST = ''
        # must be input parameter @TODO
        self.PORT = 9999
        # flag set when we want the process to exit
        self.exit = False

    def set_exit(self):
        # Grab the lock to the list of sockets
        self.lock.acquire()
        try:
            # Fill list with socket information
            self.exit = True
        finally:
            # Release the list of sockets
            self.lock.release()

    def is_exit(self):
        # Grab the lock to the list of sockets
        isexit = False
        self.lock.acquire()
        try:
            # Fill list with socket information
            isexit = self.exit
        finally:
            # Release the list of sockets
            self.lock.release()
        return isexit

    def SocketServer(self):
        """ Infinite loop listening for new incoming socket connections """
        ADDR = (self.HOST, self.PORT)
        self.serversock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.serversock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.serversock.bind(ADDR)
        self.serversock.listen(5)
        while 1:
            # Check exit flag on each loop
            if self.is_exit():
                return

            if self.SOCKET_DEBUG:
                print('waiting for connection...')

            # Blocks until new connection
            clientsock, addr = self.serversock.accept()

            # New socket must have a timeout for blocking connections
            clientsock.settimeout(1.0)

            # Handshake
            try:
                clientsock.send("OpenConn")
                # Recieve data (returned data not used yet but needs to do it)
                clientsock.recv(self.BUFF)
            except socket.timeout:
                # If failed, it probably means timeout situation
                clientsock.close()

            if self.SOCKET_DEBUG:
                print('...connected from:', addr)

            # Add connection to member variable
            self.lock.acquire()
            try:
                self.socketList.append(clientsock)
            finally:
                self.lock.release()

            #self.WriteSocketsToFile();
        return

    #def GetSocketsFromFile(self):
    #    # Read the log file and return the list of entries
    #    filename = "sockets.txt"
    #    logs = ["No Entires"]
    #    with open(filename, "r") as myfile:
    #        logs = [x.strip('\n') for x in myfile.readlines()]
    #        myfile.close()
    #    return logs

    #def WriteSocketsToFile(self):
    #    # Write all current sockets to a log file
    #    # Grab the lock to the list of sockets
    #    filename = "sockets.txt"
    #    with open(filename, "w+") as myfile:
    #        self.lock.acquire()
    #        try:
    #            index = 0
    #            destroyList = []
    #            for x in self.socketList:
    #                myfile.write( x.getpeername()[0] + "\n" )
    #        finally:
    #            # Release the list of sockets
    #            self.lock.release()
    #        myfile.close()
    #    return

    def SendToSockets(self, message):
        # Send DING/DONG to all sockets
        # Grab the lock to the list of sockets
        self.lock.acquire()
        try:
            # Send DING message to socket in another
            # thread so it doesn't interrup us
            t = threading.Thread(
                target=self.SendToSocketsThreaded,
                args=(message,)
            )
            t.start()
        finally:
            # Release the list of sockets
            self.lock.release()
        return

    def SendToSocketsThreaded(self, message):
        # Send DING to all sockets
        index = 0
        destroyList = []
        for s in self.socketList:
            result = self.SendToSocket(s, message)
            if result is None:
                destroyList.append(index)

        # Loop list to remove NULL sockets that timed out in first loop.
        # reverse list so we remove items in reverse order
        destroyList.reverse()
        for i in destroyList:
            self.socketList.pop(i)
        return

    def SendToSocket(self, s, message):
        if s is not None:
            try:
                # Send message to socket
                s.send(message)
                # Wait for response, if timeout occurs,
                # we must flag this socket as inactive
                # Recieved data not used, but need to get it anyway
                s.recv(self.BUFF)
            except socket.timeout:
                # Timeout occured
                s.shutdown(socket.SHUT_RDWR)
                s.close()
                s = None
        return s

    def get_socket_list(self):
        # Return a list of string host names that are connected to this doorbell
        list = []
        # Grab the lock to the list of sockets
        self.lock.acquire()
        try:
            # Fill list with socket information
            for x in self.socketList:
                if x is not None:
                    #list.append( socket.gethostname() )
                    list.append(x.getpeername()[0])
                else:
                    list.append("Empty Socket")
        finally:
            # Release the list of sockets
            self.lock.release()
        if not list:
            list = ["No open Sockets"]
        return list

    def SendEmail(self):
        # Attempt to send an email notification
        # Note that the TO variable must be a list, and that you have
        # to add the From, To, and Subject headers to the message yourself
        LOGIN = "EMAIL@EMAIL.COM"
        PASSWORD = "PASSWORD"

        FROMADDR = "EMAIL@EMAIL.COM"
        TOADDRS = ["EMAIL@EMAIL.COM"]
        SUBJECT = "Doorbell Pressed"
        #TEXT = "The doorbell was just pressed."

        # Prepare message headers
        msg = (
            "From: %s\r\nTo: %s\r\nSubject: %s\r\n\r\n"
            % (FROMADDR, ", ".join(TOADDRS), SUBJECT)
        )

        # Message body
        localtime = time.asctime(time.localtime(time.time()))
        msg += "Doorbell pressed (" + localtime + ")\r\n"

        # Send the mail
        try:
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.set_debuglevel(0)  # Debug output == 1
            server.ehlo()
            server.starttls()
            server.login(LOGIN, PASSWORD)
            server.sendmail(FROMADDR, TOADDRS, msg)
            server.quit()
            if self.DEBUG:
                print("Successfully sent email")
        except (KeyboardInterrupt, SystemExit):
            if self.DEBUG:
                print("Error: unable to send email")
        return

    def Ding(self):
        # Thin out audio playing list
        self.processPlaying(self.playing, self.limit_number)
        # Send DING to all sockets
        self.SendToSockets("DING")
        # Turn LED ON and play sound
        GPIO.output(self.pin_led, True)

    def Dong(self):
        # Thin out audio playing list
        self.processPlaying(self.playing, self.limit_number)
        # Send DING to all sockets
        self.SendToSockets("DONG")
        # Turn LED OFF and play sound
        GPIO.output(self.pin_led, False)

    def tick(self):
        # Called every second
        if (self.DEBUG):
            print("Tick called")

        # Calculate time since last clicked
        time_now = time.time()
        time_pressed_diff = time_now - self.time_pressed_last
        time_released_diff = time_now - self.time_released_last

        # Check to see if currently pressed AND pressed over a set time ago
        pin_value = GPIO.input(self.pin_button)
        if (
            time_pressed_diff < time_released_diff
            and time_pressed_diff >= self.time_held_limit
            and pin_value
        ):
            # Veto next release
            self.buttonReleased(0)
            self.veto_release = True

        # Sanitise the playing list
        self.processPlaying(self.playing, self.limit_number)

    def processPlaying(self, playing, limit_number):
        if (self.DEBUG):
            print("Process Playing called")

        # Remove finished processes and limit processes to a set number
        count = len(playing)
        if (count >= limit_number):
            # Remove the first few until process count is low enough
            for n in range(0, (count-limit_number)):
                item = playing[0]
                if item.poll() is None:
                    item.terminate()  # Wasnt finished, make it finished
                playing.pop(0)  # remove first item from list

    def button(self, channel):
        # Button has been either pressed or released
        # Its a rising or falling edge, check pin value to see which
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
            time_diff >= self.time_gap
            and not self.veto_release
            and self.isPressed
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
        # Append to file (will create if didnt already exist)
        filename = "doorbell.txt"
        with open(filename, "a+") as myfile:
            localtime = time.asctime(time.localtime(time.time()))
            myfile.write("Doorbell " + localtime + "\n")
            myfile.close()

    def GetLogsFromFile(self):
        # Read the log file and return the list of entries
        filename = "doorbell.txt"
        logs = ["No Entires"]
        with open(filename, "r") as myfile:
            logs = [x.strip('\n') for x in myfile.readlines()]
            myfile.close()
        # Log is returned in ascending date.
        # We want it reversed
        logs.reverse()
        return logs

    def main(self):
        if (self.DEBUG):
            print("Started")
        try:
            #set up GPIO using BCM numbering
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
            while True:
                # Check exit flag on each loop
                if self.is_exit():
                    return

                self.tick()
                if loopCount >= 60:
                    # Send PING to all sockets
                    loopCount = 0
                    if (self.DEBUG):
                        print("PING")
                    self.SendToSockets("PING")

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

#if __name__=="__main__":
#    # Instantiate doobell class
#    DB = DoorBell_Server()
#
#    # Kick off new thread listening for doorbell events
#    t1 = threading.Thread(target=DB.main)
#    t1.start()
#
#    # Kick off new thread listening for new sockets
#    t2 = threading.Thread(target=DB.SocketServer)
#    t2.start()
