#!/usr/bin/env python
import time
import threading


class LedStrip():

    def __init__(self, blink_stick, channel):
        # Constructor
        self.blinkstick = blink_stick
        # LED On flag
        self.led_on = False
        # LED ON Colour
        self.led_red = 255
        self.led_green = 255
        self.led_blue = 100
        # Current LED Colour
        self.current_led_red = 0
        self.current_led_green = 0
        self.current_led_blue = 0
        # Channel R,B,G == 0,1,2
        self.channel = channel
        # Thread lock
        self.lock = threading.Lock()
        self.exit = False  # flag set when we want the process to exit
        # Debug flag
        self.DEBUG = False

    def set_exit(self):
        """ Tell this thread to stop """
        # Grab the lock to the list of sockets
        self.lock.acquire()
        try:
            # Fill list with socket information
            self.exit = True
        finally:
            # Release the list of sockets
            self.lock.release()

    def is_exit(self):
        """ Has this thread been told to stop """
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

    def get_led_colour(self):
        """ Get the LED RGB Values """
        self.lock.acquire()
        try:
            red = self.led_red
            green = self.led_green
            blue = self.led_blue
        finally:
            self.lock.release()
        return red, green, blue

    def set_led_colour(self, red, green, blue):
        """ Set the LED RGB Values """
        self.lock.acquire()
        try:
            self.led_red = red
            self.led_green = green
            self.led_blue = blue
        finally:
            self.lock.release()
        return

    def get_current_led_colour(self):
        """ Get the current working LED RGB Values """
        self.lock.acquire()
        try:
            red = self.current_led_red
            green = self.current_led_green
            blue = self.current_led_blue
        finally:
            self.lock.release()
        return red, green, blue

    def set_current_led_colour(self, red, green, blue):
        """ Set the current working LED RGB Values """
        self.lock.acquire()
        try:
            self.current_led_red = red
            self.current_led_green = green
            self.current_led_blue = blue
        finally:
            self.lock.release()
        return

    def isOn(self):
        """ Are the LEDs on """
        led_on = False
        self.lock.acquire()
        try:
            led_on = self.led_on
        finally:
            self.lock.release()
        return led_on

    def setOn(self, led_on):
        """ Set the LEDs on flag """
        self.lock.acquire()
        try:
            self.led_on = led_on
        finally:
            self.lock.release()
        return

    def setAll(self, red, green, blue):
        """ Set all leds to a specific colour """
        if self.DEBUG:
            print("Colour ", str(red), str(green), str(blue))
        # Loop leds and set RGB values
        for i in range(0, self.blinkstick.r_led_count):
            self.blinkstick.set_color(self.channel, i, red, green, blue)
        # Single call to send RGB values to blinkstick
        self.send_data_all()
        # Update what colour this class thinks its set too.
        self.set_current_led_colour(red, green, blue)
        return

    def phaseLights(self, fromR, fromG, fromB, toR, toG, toB):
        """ Gently change leds from a set color to another colour """
        timeSpan = 1.0  # seconds
        steps = 50  # static number of steps
        interval = timeSpan / steps

        # Calculate difference for each colour band
        red_diff = toR-fromR
        green_diff = toG-fromG
        blue_diff = toB-fromB

        # Using band difference, calculate
        # interval per colour band for each step
        red_int = (float(red_diff) / steps)
        green_int = (float(green_diff) / steps)
        blue_int = (float(blue_diff) / steps)

        if self.DEBUG:
            print("Interval ", str(red_int), str(green_int), str(blue_int))

        # Set the leds colour for each step
        red = float(fromR)
        green = float(fromG)
        blue = float(fromB)
        for i in range(0, steps):
            self.setAll(int(red), int(green), int(blue))
            red += red_int
            green += green_int
            blue += blue_int
            time.sleep(interval)

        # Finally, ensure we reach the final colour
        self.setAll(toR, toG, toB)

    def switch_on(self):
        """ Switch the lights on (if not already on) """
        if not self.is_on():
            # Get current LED colour and colour it should be
            r, g, b = self.get_led_colour()
            current_r, current_g, current_b = self.get_current_led_colour()
            # Phase the lights from current to new values
            self.phaseLights(current_r, current_g, current_b, r, g, b)
            # Set flag
            self.setOn(True)

    def switch_off(self):
        """ Switch the lights off (if not already off) """
        if self.is_on():
            # Get current LED colour and colour it should be
            current_r, current_g, current_b = self.get_current_led_colour()
            # Phase the lights from current to new values
            self.phaseLights(current_r, current_g, current_b, 0, 0, 0)
            # Set flag
            self.setOn(False)
