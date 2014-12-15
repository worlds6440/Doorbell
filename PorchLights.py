import time
from blinkstick import blinkstick
import threading

class PorchLights(blinkstick.BlinkStickPro):

	def constructor(self):
		# Member Vars
		self.DEBUG = False	
		# LED On/Off flag
		self.LEDOn = False
		# Time for LED to turn ON
		self.onHour = 16
		self.onMin = 00
		# Time for LED to turn OFF
		self.offHour = 00
		self.offMin = 00
		# LED ON Colour
		self.led_red = 255
		self.led_green = 255
		self.led_blue = 100
		# Current LED Colour
		self.current_led_red = 0
		self.current_led_green = 0
		self.current_led_blue = 0
		# Thread lock
		self.lock = threading.Lock()
		self.exit = False # flag set when we want the process to exit
	
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
	
	def get_led_colour(self):
		# Get the LED RGB Values
		self.lock.acquire()
		try:
			red = self.led_red
			green = self.led_green
			blue = self.led_blue
		finally:
			self.lock.release()
		return red, green, blue
		
	def set_led_colour(self, red, green, blue):
		# Get the LED RGB Values
		self.lock.acquire()
		try:
			self.led_red = red
			self.led_green = green
			self.led_blue = blue
		finally:
			self.lock.release()
		return
		
	def get_current_led_colour(self):
		# Get the LED RGB Values
		self.lock.acquire()
		try:
			red = self.current_led_red
			green = self.current_led_green
			blue = self.current_led_blue
		finally:
			self.lock.release()
		return red, green, blue
		
	def set_current_led_colour(self, red, green, blue):
		# Get the LED RGB Values
		self.lock.acquire()
		try:
			self.current_led_red = red
			self.current_led_green = green
			self.current_led_blue = blue
		finally:
			self.lock.release()
		return
		
	def isOn(self):
		# Get the LED RGB Values
		led_on = False
		self.lock.acquire()
		try:
			led_on = self.LEDOn
		finally:
			self.lock.release()
		return led_on
		
	def setOn(self, led_on):
		# Get the LED RGB Values
		self.lock.acquire()
		try:
			self.LEDOn = led_on
		finally:
			self.lock.release()
		return

	def setAll(self, red, green, blue):
		# Set all leds to a specific colour
		if self.DEBUG:
			print("Colour ", str(red), str(green), str(blue))
		# Loop leds and set RGB values
		for i in range(0, self.r_led_count):
			self.set_color(0, i, red, green, blue)
		# Single call to send RGB values to blinkstick
		self.send_data_all()
		# Update what colour this class thinks its set too.
		self.set_current_led_colour(red, green, blue)
		return

	def phaseLights(self, fromR, fromG, fromB, toR, toG, toB):
		# Gently change leds from a set color to another colour
		timeSpan = 1.0 # seconds
		steps = 50 # static number of steps
		interval = timeSpan / steps

		# Calculate difference for each colour band
		red_diff = toR-fromR
		green_diff = toG-fromG
		blue_diff = toB-fromB

		# Using band difference, calculate interval per colour band for each step
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

		return

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
			if not self.connect():
				# Failed to connect to USB blinkstick.
				# Report error and sleep for a little bit before trying again.
				print "No BlinkSticks found"
				time.sleep(60)
			else:
				# Connected successfully, Ensure all remnant 
				# commands are sent to stick before use.
				self.send_data_all()
				
				# Ensure lights are off to start
				self.setAll(0, 0, 0)
				try:
					# Loop indefinitely
					while True:
						# Check exit flag on each loop
						if self.is_exit():
							return
				
						# Get the time now
						timeNow = time.localtime()

						# Find out if the LEDS should be on
						shouldBeOn = self.shouldBeOn(timeNow)
						
						# Get colour LEDs should be and what they actually are
						led_red, led_green, led_blue = self.get_led_colour()
						current_led_red, current_led_green, current_led_blue = self.get_current_led_colour()

						# Test whether LEDS are on or not
						led_on = self.isOn()
						
						# Test whether the LEDs have changed colour
						colour_changed = False
						if led_red != current_led_red or led_green != current_led_green or led_blue != current_led_blue:
							colour_changed = True
							
						if shouldBeOn and (not led_on or colour_changed):
							# Turn light ON
							#self.phaseLights(0,0,0, led_red, led_green, led_blue)
							#self.LEDOn = True
							self.phaseLights(current_led_red, current_led_green, current_led_blue, led_red, led_green, led_blue)
							self.setOn(True)
						elif not shouldBeOn and led_on:
							# Turn light OFF
							self.phaseLights(self.led_red, self.led_green, self.led_blue, 0,0,0)
							#self.LEDOn = False
							self.setOn(False)

						# Sleep for a minute and test again.
						# NOTE: will always normalise the tick to round minutes
						time.sleep(60 - timeNow.tm_sec)

				except KeyboardInterrupt:
					# Users pressed Ctrl+C
					self.off()
					return
		return

#if __name__=="__main__":
#	# Change the number of LEDs for r_led_count
#	main = PorchLights(r_led_count=5, max_rgb_value=255)
#	main.constructor()
#	main.run()
