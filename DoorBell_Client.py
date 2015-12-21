#!/usr/bin/env python
import sys
import threading
import subprocess
import RPi.GPIO as GPIO
import time
import socket
import PorchLights
import os

class DoorBell_Client:
	def __init__(self):
		# Constructor
		# Member variables
		self.DEBUG = False
		self.playing = [] # List of dings and dongs
		self.limit_number = 4
		self.s = None
		self.lastPing = time.time()
		self.lock = threading.Lock()
		
		self.selected_ding = "startrek-doorbell-nextgen.wav"
		self.selected_dong = ""

		self.BUFF = 1024
		self.HOST = '192.168.1.248'# must be input parameter @TODO
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
		
	def get_wav_options(self):
		# return a string list of wav filenames from the sounds folder
		dir_list = os.listdir( os.path.join(os.path.dirname(__file__), 'sounds/') )
		return dir_list
		
	def get_selected_ding(self):
		# Return the string filename of the current DING sound
		ding = ""
		self.lock.acquire()
		try:
			# Fill list with socket information
			ding = self.selected_ding
		finally:
			# Release the list of sockets
			self.lock.release()
		return ding
		
	def get_selected_dong(self):
		# Return the string filename of the current DONG sound
		dong = ""
		self.lock.acquire()
		try:
			# Fill list with socket information
			dong = self.selected_dong
		finally:
			# Release the list of sockets
			self.lock.release()
		return dong
		
	def set_selected_ding(self, wav):
		# Set the string filename of the current DING sound
		self.lock.acquire()
		try:
			# Fill list with socket information
			self.selected_ding = wav
		finally:
			# Release the list of sockets
			self.lock.release()
		return
		
	def set_selected_dong(self, wav):
		# Set the string filename of the current DONG sound
		self.lock.acquire()
		try:
			# Fill list with socket information
			self.selected_dong = wav
		finally:
			# Release the list of sockets
			self.lock.release()
		return
	
	def SocketClient(self):

		# Look infinitely waiting for socket data
		bQuit = False
		while not bQuit:
			# Check exit flag on each loop
			if self.is_exit():
				return
		
			# If no socket, create one and try to connect
			if self.s == None:
				if self.DEBUG:
					print("Connecting to :", self.HOST)
				ADDR = (self.HOST, self.PORT)
				self.s = socket.socket()
				try:
					self.s.connect(ADDR)
					if self.DEBUG:
						print("Connected")
				except:
					self.s = None
			if self.s != None:
				try:
					# Wait for socket data
					rec_data = self.s.recv(self.BUFF)

					if self.DEBUG:
						print(rec_data.lstrip())

					if rec_data.lstrip() == "OpenConn":
						# Return handshake response
						self.s.send("OpenConn")
	
					elif rec_data.lstrip() == "DING":
						# Return handshake response
						self.s.send("DING")
						self.Ding()
	
					elif rec_data.lstrip() == "DONG":
						# Return handshake response
						self.s.send("DONG")
						self.Dong()

					elif rec_data.lstrip() == "PING":
						# Return handshake response
						self.s.send("PING")

					# Remember the last communication time
					lastPing = time.time()

				except KeyboardInterrupt:
					# CTRL-C pressed, shut everything down
					self.lock.acquire()
					try:
						self.s.shutdown(socket.SHUT_RDWR)
						self.s.close()
						self.s = None
						bQuit = True
					finally:
						self.lock.release()
					if self.DEBUG:
						print("User hit ctrl-c")
				except socket.error as e:
					# Socket error
					self.lock.acquire()
					try:
						self.s.shutdown(socket.SHUT_RDWR)
						self.s.close()
						self.s = None
					finally:
						self.lock.release()
					if self.DEBUG:
						print("Socket Error")
			else:
				# Sleep so we dont retry instantly
				time.sleep(1)
		return

	def Ding(self):
		# Thin out audio playing list
		self.processPlaying(self.playing, self.limit_number)
		filename = 'sounds/' + self.selected_ding
		if self.selected_ding!="" and os.path.isfile(filename):
			self.playing.append( subprocess.Popen([ "/usr/bin/aplay", '-q', filename ]) )
		return

	def Dong(self):
		# Thin out audio playing list
		self.processPlaying(self.playing, self.limit_number)
		filename = 'sounds/' + self.selected_dong
		if self.selected_dong!="" and os.path.isfile(filename):
			self.playing.append( subprocess.Popen([ "/usr/bin/aplay", '-q', filename ]) )
		return

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
					item.terminate() # Wasnt finished, make it finished
				playing.pop(0) # remove first item from list

	def PingCheck(self):
		# Loop constantly, periodically checking 
		# time since last communication.
		while True:
			timeNow = time.time()
			diff = timeNow - self.lastPing
			if diff >= 300:
				# Socket has timed out, kill connection
				self.lock.acquire()
				try:
					self.s.shutdown(socket.SHUT_RDWR)
					self.s.close()
					self.s = None
				finally:
					self.lock.release()
			sleep(60)

#if __name__=="__main__":
#	# Change the number of LEDs for r_led_count
#	PL = PorchLights.PorchLights(r_led_count=5, max_rgb_value=255)
#
#	# Kick off new thread to control the lights
#	t1 = threading.Thread(target=PL.run)
#	t1.start()
#
#	# Instantiate doobell class
#	DB = DoorBell_Client()	
#	DB.SocketClient()

