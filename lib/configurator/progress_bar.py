#!/usr/bin/env python
import threading
import time
import os, sys


class ThreadingSpinning(object):
	""" Threading example class
	The run() method will be started and it will run in the background
	until the application exits.
	"""

	def __init__(self, tmpfile):
		""" Constructor
		:type interval: int
		:param interval: Check interval, in seconds
		"""
		self.interval = 0.1 
		self.tmpfile = tmpfile

		thread = threading.Thread(target=self.run, args=())
		thread.daemon = True                            # Daemonize thread
		thread.start()                                  # Start the execution

	def check_stop(self):
		if os.path.isfile(self.tmpfile):
			return False
		else:
			return True

	def spinning_cursor(self):
		while True:
			for cursor in '|/-\\':
				yield cursor

	def run(self):
		""" Method that runs forever """
		spinner = self.spinning_cursor()
		while True:
			sys.stdout.write(spinner.next())
			sys.stdout.flush()
			time.sleep(self.interval)
			sys.stdout.write('\b')
			if self.check_stop():
				break

# vim: tabstop=8 shiftwidth=8 softtabstop=8 noexpandtab
