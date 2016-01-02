#!/usr/bin/env python
import time
import threading
from random import randint


class LedStrip():

    def __init__(self, blink_stick, channel, allow_seasonal_display=None):
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
        # LED illumination mode enum values
        self.led_mode_standard = 1
        self.led_mode_christmas = 2
        # LED illumination mode
        self.led_mode = self.led_mode_standard
        self.allow_seasonal_display = False
        if allow_seasonal_display is not None:
            self.allow_seasonal_display = allow_seasonal_display
        # Thread pointer for christmas display (and any future mode)
        self.led_thread = None

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
        return self.exit

    def get_led_colour(self):
        """ Get the LED RGB Values """
        red = self.led_red
        green = self.led_green
        blue = self.led_blue
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
        # If LED already on, change colour immediately
        if self.is_on():
            self.set_all(red, green, blue)
        return

    def get_current_led_colour(self):
        """ Get the current working LED RGB Values """
        red = self.current_led_red
        green = self.current_led_green
        blue = self.current_led_blue
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

    def is_on(self):
        """ Are the LEDs on """
        return self.led_on

    def set_on(self, led_on):
        """ Set the LEDs on flag """
        self.lock.acquire()
        try:
            self.led_on = led_on
        finally:
            self.lock.release()
        return

    def led_count(self):
        # Get appropriate LED count for current channel
        led_count = 0
        if self.channel == 0:
            led_count = self.blinkstick.r_led_count
        if self.channel == 1:
            led_count = self.blinkstick.g_led_count
        if self.channel == 2:
            led_count = self.blinkstick.b_led_count
        return led_count

    def set_all(self, red, green, blue):
        """ Set all leds to a specific colour """
        if self.DEBUG:
            print("Colour ", str(red), str(green), str(blue))

        # Get appropriate LED count for current channel
        led_count = self.led_count()

        self.lock.acquire()
        try:
            # Loop leds and set RGB values
            for i in range(0, led_count):
                self.blinkstick.set_color(self.channel, i, red, green, blue)
            # Single call to send RGB values to blinkstick
            self.blinkstick.send_data_all()
        finally:
            self.lock.release()
        # Update what colour this class thinks its set too.
        self.set_current_led_colour(red, green, blue)
        return

    def phase_lights(self, fromR, fromG, fromB, toR, toG, toB):
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
            self.set_all(int(red), int(green), int(blue))
            red += red_int
            green += green_int
            blue += blue_int
            time.sleep(interval)

        # Finally, ensure we reach the final colour
        self.set_all(toR, toG, toB)

    def switch_on(self, force=False):
        """ Switch the lights on (if not already on) """
        if not self.is_on() or force:
            if self.led_mode == self.led_mode_standard:
                # Get current LED colour and colour it should be
                r, g, b = self.get_led_colour()
                current_r, current_g, current_b = self.get_current_led_colour()
                # Phase the lights from current to new values
                self.phase_lights(current_r, current_g, current_b, r, g, b)

            if self.led_mode == self.led_mode_christmas:
                # Kick off internal thread to constantly change lights
                if self.led_thread is None:
                    # Ensure thread killing flag is cleared
                    self.exit = False
                    # Kick off new thread listening for doorbell events
                    self.led_thread = threading.Thread(
                        target=self.christmas_display_1
                        #target=self.christmas_display_2
                    )
                    self.led_thread.start()
            # Set flag
            self.set_on(True)

    def switch_off(self, force=False):
        """ Switch the lights off (if not already off) """
        if self.is_on() or force:
            if self.led_thread is None:
                # Get current LED colour and colour it should be
                current_r, current_g, current_b = self.get_current_led_colour()
                # Phase the lights from current to new values
                self.phase_lights(current_r, current_g, current_b, 0, 0, 0)
            else:
                # ensure thread is killed
                self.set_exit()
                # Wipe thread pointer
                self.led_thread = None
            # Set flag
            self.set_on(False)

    def effect_set_even_odd(self, red=None, green=None, blue=None, even=True):
        """ Set all even indexed LEDs a certain colour """
        # Maximum R G or B value
        max_value = 255

        r = 0
        g = 0
        b = 0

        # Choose a random colour limited to between 0 and 255
        if red is None:
            r = randint(0, max_value)
        else:
            r = red
        if green is None:
            g = randint(0, max_value)
        else:
            g = green
        if blue is None:
            b = randint(0, max_value)
        else:
            b = blue

        led_count = self.led_count()

        # Send to LEDs
        self.lock.acquire()
        try:
            # Calculate start index depending on whether
            # working with even or odd numbers
            from_index = 0
            if not even:
                from_index = 1
            # Set every other LED to the required colour
            for i in range(from_index, (led_count-1), 2):
                    self.blinkstick.set_color(self.channel, i, r, g, b)
        finally:
            self.lock.release()

    def effect_swipe(self, red=None, green=None, blue=None, forwards=True):
        """ Turn all LEDs on in a swiping motion """
        # Maximum R G or B value
        max_value = 255

        r = 0
        g = 0
        b = 0

        # Choose a random colour limited to between 0 and 255
        if red is None:
            r = randint(0, max_value)
        else:
            r = red
        if green is None:
            g = randint(0, max_value)
        else:
            g = green
        if blue is None:
            b = randint(0, max_value)
        else:
            b = blue

        # calculate loop range for forwards or backwards
        led_count = self.led_count()
        from_index = 0
        to_index = led_count
        if not forwards:
            from_index = led_count-1
            to_index = -1

        # Loop LED indices
        x = from_index
        while x != to_index:
            self.lock.acquire()
            try:
                # Set LEDs colour
                self.blinkstick.set_color(self.channel, x, r, g, b)
                # Single call to send RGB values to blinkstick
                self.blinkstick.send_data_all()
            finally:
                self.lock.release()
            # Sleep a small while between each LED setting
            time.sleep(0.05)
            # Increment loop index
            if forwards:
                x = x+1
            else:
                x = x-1

    def christmas_display_1(self):
        """ Loop indefinitely displaying
        christmassy themed lighting display """
        while True:
            # Check exit flag on each loop
            if self.is_exit():
                # Turn LEDs off if display exited
                self.set_all(0, 0, 0)
                return

            self.effect_set_even_odd(255, 0, 0, even=True)
            self.effect_set_even_odd(0, 255, 0, even=False)
            # Pause for a small time
            time.sleep(0.5)

            self.effect_set_even_odd(0, 255, 0, even=True)
            self.effect_set_even_odd(255, 0, 0, even=False)
            # Pause for a small time
            time.sleep(0.5)

    def christmas_display_2(self):
        try:
            forwards = True
            while True:
                # Check exit flag on each loop
                if self.is_exit():
                    # Turn LEDs off if display exited
                    self.set_all(0, 0, 0)
                    return

                # Swipe the LEDs on with random colours
                self.effect_swipe(
                    red=None,
                    green=None,
                    blue=None,
                    forwards=forwards
                )
                # Sleep a small while between each LED setting
                time.sleep(0.05)
                # Swipe the LEDs off
                self.effect_swipe(
                    red=0,
                    green=0,
                    blue=0,
                    forwards=forwards
                )
                # Invert forwards flag each time
                forwards = not forwards

        except KeyboardInterrupt:
            self.off()
            return
