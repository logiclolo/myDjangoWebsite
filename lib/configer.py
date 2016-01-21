#!/usr/bin/env python

import sys, os
import re 
import subprocess
from copy import deepcopy
from os import environ
import signal
import getpass
import time

class Configer(object):

	def __init__(self, model):
		flash_base = os.path.join(os.getenv('PRODUCTDIR'), 'flashfs_base')  
		self.cdf = os.path.join(flash_base, model, 'etc', 'CDF.xml')
		self.prefix_etc = os.path.join(flash_base, model)

		self.start()

	def start(self):
		# skip if configer is already in background
		check = self.get_configer_from_ps()
		if check.readline() != '':
			return None

		ld_library_path = os.path.join(os.getcwd(), 'configer', 'lib') 
		env = dict(os.environ)
		env['LD_LIBRARY_PATH'] = ld_library_path

		#p = subprocess.Popen('LD_LIBRARY_PATH=%s ./configer/configer -d -i %s -e %s' % (ld_library_path, self.cdf, self.prefix_etc), shell=True)
		p = subprocess.Popen(('./configer/configer', '-d', '-i', self.cdf, '-e', self.prefix_etc), env=env)

		time.sleep(0.02)

		return p

	def get_configer_from_ps(self):
		user = getpass.getuser()
		cmd = 'ps aux | grep %s | grep "configer/configer" | grep -v grep' % user
		results = subprocess.Popen(cmd, shell=True, stdout = subprocess.PIPE).stdout

		return results

	def stop(self):

		# this can't terminate the configer process because of the wrong pid
		# it need to be check

		#subprocess_p.terminate()

		# workaround
		# use 'ps' to get the configer process and terminate it

		check = self.get_configer_from_ps()
		for c in check:
			pid = c.split()[1]
			pid = int(pid)
			os.kill(pid, signal.SIGTERM)

	def confclient(self, param):
		devnull = open(os.devnull, 'wb')
		return subprocess.Popen('./configer/confclient -x %s' % param, shell=True, stdout = subprocess.PIPE, stderr=devnull)

	def fetch_value(self, param):

		ret = '' 
		retry = 1000 
		client = None
		configer = None

		while ret == '' and retry != 0:
			client = self.confclient(param) 
			client.wait()
			returncode = client.returncode

			ret = client.stdout.read()
			ret = re.sub('\n', '', ret)
			retry = retry - 1

			if retry == 0 or returncode == 1:
				return None
			else:
				time.sleep(0.01)

		if ret == '':
			return None
		else:
			return ret


# vim: tabstop=8 shiftwidth=8 softtabstop=8 noexpandtab
