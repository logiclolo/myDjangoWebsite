#!/usr/bin/env python

import sys, os
import re 
import subprocess
from copy import deepcopy
from os import environ
import signal
import getpass
import time

class configer(object):

	def __init__(self, model):
		flash_base = os.path.join(os.getenv('PRODUCTDIR'), 'flashfs_base')  
		self.cdf = os.path.join(flash_base, model, 'etc', 'CDF.xml')
		self.prefix_etc = os.path.join(flash_base, model)

	def start(self):
		ld_library_path = os.path.join(os.getcwd(), 'configer', 'lib') 
		env = dict(os.environ)
		env['LD_LIBRARY_PATH'] = ld_library_path
		#p = subprocess.Popen('LD_LIBRARY_PATH=%s ./configer/configer -d -i %s -e %s' % (ld_library_path, self.cdf, self.prefix_etc), shell=True)
		p = subprocess.Popen(('./configer/configer', '-d', '-i', self.cdf, '-e', self.prefix_etc), env=env)
		p.wait()

		#print p.pid
		return p

	def stop(self, subprocess_p):

		# this can't terminate the configer process because of the wrong pid
		#subprocess_p.terminate()

		# workaround
		# use 'ps' to get the configer process and terminate it
		user = getpass.getuser()
		results = subprocess.Popen('ps aux | grep %s | grep "configer/configer" | grep -v grep' % user, shell=True, stdout = subprocess.PIPE).stdout
		for r in results:
			pid = r.split()[1]
			pid = int(pid)
			os.kill(pid, signal.SIGTERM)

	def confclient(self, param):
		return subprocess.Popen('./configer/confclient -p 99 -t Value -g %s' % param, shell=True, stdout = subprocess.PIPE)

	def fetch_value(self, param):

		ret = None
		returncode = '' 
		retry = 5
		client = None
		configer = None

		configer = self.start()

		while returncode != 0 and retry != 0:
			client = self.confclient(param) 
			client.wait()
			returncode = client.returncode
			retry = retry - 1
			if retry == 0:
				self.stop(configer)
				return None
			#time.sleep(1)

		for out in client.stdout: 	
			out = re.sub('\n', '', out)
			ret = out 

		self.stop(configer)

		return ret


# vim: tabstop=8 shiftwidth=8 softtabstop=8 noexpandtab
