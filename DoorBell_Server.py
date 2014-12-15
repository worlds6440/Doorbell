import sys
import threading
import subprocess
import RPi.GPIO as GPIO
import time
import socket

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
		self.time_pressed_last = time.time()
		self.time_released_last = time.time()
		self.time_gap = 0.1 # time gap in seconds
		self.playing = [] # List of dings and dongs
		self.limit_number = 4
		self.time_held_limit = 1 # max time allowed for holding button
		self.isPressed = False
		self.veto_release = False
		self.socketList = [] # List of open connections
		self.lock = threading.Lock()

		self.BUFF = 1024
		self.HOST = '' #'127.0.0.1'# must be input parameter @TODO
		self.PORT = 9999 # must be input parameter @TODO
		
		self.exit = False # flag set when we want the process to exit
		return
		
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
		# Infinite loop listening for new incoming socket connections
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
				rec_data = clientsock.recv(self.BUFF)
			except timeout:
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
		return

	def SendToSockets(self, message):
		# Send DING/DONG to all sockets
		# Grab the lock to the list of sockets
		self.lock.acquire()
		try:
			# Send DING message to socket in another thread so it doesn't interrup us
			t = threading.Thread(target=self.SendToSocketsThreaded, args=(message,))
			t.start()
		finally:
			# Release the list of sockets
			self.lock.release()
		return

	def SendToSocketsThreaded(self, message):
		# Send DING to all sockets
		index = 0
		destroyList = []
		for socket in self.socketList:
			result = self.SendToSocket(socket, message)
			if result == None:
				destroyList.append(index)

		# Loop list to remove NULL sockets that timed out in first loop
		destroyList.reverse() # reverse list so we remove items in reverse order
		for i in destroyList:
			self.socketList.pop(i)
		return

	def SendToSocket(self, s, message):
		if socket != None:
			try:
				# Send message to socket
				s.send(message)
				# Wait for response, if timeout occurs, we must flag this socket as inactive
				rec_data = s.recv(self.BUFF)
			except timeout:
				# Timeout occured
				s.shutdown(socket.SHUT_RDWR)
				s.close()
				s = None
		return s

	def get_socket_list(self):
		# Return a list of string host names that are connected to this doorbell
		list = [] #["192.168.1.248", "192.168.1.59"]		
		# Grab the lock to the list of sockets
		self.lock.acquire()
		try:
			# Fill list with socket information
			for socket in self.socketList:
				list.append( socket.gethostname() )
		finally:
			# Release the list of sockets
			self.lock.release()
		return list
	
	def Ding(self):
		# Thin out audio playing list
		self.processPlaying(self.playing, self.limit_number)

		# Send DING to all sockets
		self.SendToSockets("DING")

		# Turn LED ON and play sound
		GPIO.output(self.pin_led, True)
		#self.playing.append( subprocess.Popen([ "/usr/bin/aplay", '-q', 'ding.wav' ]) )
		return

	def Dong(self):
		# Thin out audio playing list
		self.processPlaying(self.playing, self.limit_number)

		# Send DING to all sockets
		self.SendToSockets("DONG")

		# Turn LED OFF and play sound
		GPIO.output(self.pin_led, False)
		#self.playing.append( subprocess.Popen([ "/usr/bin/aplay", '-q', 'dong.wav' ]) )
		return

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
		if (time_pressed_diff < time_released_diff and time_pressed_diff >= self.time_held_limit and pin_value):
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
				if item.poll() == None:
					item.terminate() #  Wasnt finished, make it finished
				playing.pop(0) #  remove first item from list

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
			self.Ding()

			# Remember last successful button press
			self.time_pressed_last = time_now

	def buttonReleased(self, channel):
		if (self.DEBUG):
			print("Release called")

		time_now = time.time()
		time_diff = time_now - self.time_released_last
		if (time_diff >= self.time_gap and not self.veto_release and self.isPressed):
			# Time since previous press is longer than min gap
			if (self.DEBUG):
				print("Button released!")

			self.isPressed = False
			self.Dong()
			
			# Remember last successful button press
			self.time_released_last = time_now

		# Reset variable
		self.veto_release = False

	def main(self):
		if (self.DEBUG):
			print("Started")
		try:
			#set up GPIO using BCM numbering
			GPIO.setmode(GPIO.BCM)

			# Set GPIO pins appropriately
			if (self.DEBUG):
				print("GPIO Button and LED Setup")
			GPIO.setup(self.pin_button, GPIO.IN, pull_up_down = GPIO.PUD_DOWN)
			GPIO.setup(self.pin_led, GPIO.OUT)
			if (self.DEBUG):
				print("GPIO Event Callback Setup")
			GPIO.add_event_detect(self.pin_button, GPIO.BOTH, callback=self.button)
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
			print( "Error: %s" % e )
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
#	# Instantiate doobell class
#	DB = DoorBell_Server()
#	
#	# Kick off new thread listening for doorbell events
#	t1 = threading.Thread(target=DB.main)
#	t1.start()
#
#	# Kick off new thread listening for new sockets
#	t2 = threading.Thread(target=DB.SocketServer)
#	t2.start()
