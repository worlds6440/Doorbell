#!/usr/bin/env python
import time
from blinkstick import blinkstick
import threading
import LedStrip


class PorchLights():

    def __init__(self):
        # Constructor
        # Member Vars
        self.DEBUG = False
        # Time for LED to turn ON
        self.onHour = 16
        self.onMin = 00
        # Time for LED to turn OFF
        self.offHour = 00
        self.offMin = 00
        # Thread lock
        self.lock = threading.Lock()
        self.exit = False  # flag set when we want the process to exit

        # Static channel indecies
        self.channel_red = 0
        self.channel_green = 1
        self.channel_blue = 2

        # Create blinkstick instance
        self.blinkstick = blinkstick.BlinkStickPro(
            r_led_count=5,
            max_rgb_value=255
        )
        # Create empty LED strip array
        self.channel = []

        # Add Red Channel LED strip (5 leds shown above)
        self.channel.append(
            LedStrip.LedStrip(
                self.blinkstick,
                self.channel_red
            )
        )

    def set_exit(self):
        # Grab the lock to the list of sockets
        self.lock.acquire()
        try:
            # Fill list with socket information
            self.exit = True
            # Set all channel threads to exit too
            for item in self.channel:
                item.set_exit()
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

    def get_led_colour(self, channel):
        return self.channel[channel].get_led_colour()

    def set_led_colour(self, channel, red, green, blue):
        self.channel[channel].set_led_colour(red, green, blue)

    def set_all_led_colour(self, red, green, blue):
            # Set all channel threads to RGB colour
            for item in self.channel:
                self.set_led_colour(
                    item.channel,
                    red,
                    green,
                    blue
                )

    def shouldBeOn(self, timeNow):
        if self.DEBUG:
            print("HH:MM", timeNow.tm_hour, ':', timeNow.tm_min, timeNow.tm_sec)

        # Convert On/Off times to minutes of the day
        onTime = self.onHour*60 + self.onMin
        offTime = self.offHour*60 + self.offMin
        curTime = timeNow.tm_hour*60 + timeNow.tm_min

        between = False
        if onTime < offTime:
            # Looking for a time between on/off
            between = True
        elif onTime > offTime:
            # Looking for a time between off/on
            between = False
        else:
            # On and Off time are the same
            between = False

        # Test whether the time is between or outside of the allotted range
        shouldBeOn = False
        if between:
            if onTime <= curTime and curTime < offTime:
                shouldBeOn = True
        else:
            if onTime <= curTime or curTime < offTime:
                shouldBeOn = True

        return shouldBeOn

    def run(self):
        while True:
            # Connect to blinkstick
            if not self.blinkstick.connect():
                # Failed to connect to USB blinkstick.
                # Report error and sleep for a little bit before trying again.
                print("No BlinkSticks found")
                time.sleep(60)
            else:
                # Connected successfully, Ensure all remnant
                # commands are sent to stick before use.
                self.blinkstick.send_data_all()

                try:
                    # Ensure lights are off to start
                    for item in self.channel:
                        # Turn light OFF
                        item.switch_off()

                    # Loop indefinitely
                    while True:
                        # Check exit flag on each loop
                        if self.is_exit():
                            return

                        # Get the time now
                        timeNow = time.localtime()

                        # Find out if the LEDS should be on
                        shouldBeOn = self.shouldBeOn(timeNow)

                        for item in self.channel:
                            if shouldBeOn:
                                # Turn light ON
                                item.switch_on()
                            else:
                                # Turn light OFF
                                item.switch_off()

                        # Sleep for a minute and test again.
                        # NOTE: will always normalise the tick to round minutes
                        time.sleep(60 - timeNow.tm_sec)

                except (KeyboardInterrupt, SystemExit):
                    # Users pressed Ctrl+C
                    self.off()
                    return
        return

#if __name__=="__main__":
#    # Change the number of LEDs for r_led_count
#    main = PorchLights(r_led_count=5, max_rgb_value=255)
#    main.constructor()
#    main.run()
