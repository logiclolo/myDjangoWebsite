#!/usr/bin/env python

import sys, os
import re 
import subprocess
from copy import deepcopy
from os import environ
import signal
import getpass
import time

def start_configer(cdf_path, prefix_etc_path):
	ld_library_path = os.path.join(os.getcwd(), 'configer', 'lib') 
	env = dict(os.environ)
	env['LD_LIBRARY_PATH'] = ld_library_path
	#p = subprocess.Popen('LD_LIBRARY_PATH=%s ./configer/configer -d -i %s -e %s' % (ld_library_path, cdf_path, prefix_etc_path), shell=True)
	p = subprocess.Popen(('./configer/configer', '-d', '-i', cdf_path, '-e', prefix_etc_path), env=env)
	p.wait()

	#print p.pid
	return p

def stop_configer(subprocess_p):

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
		

def start_confclient(param):
	return subprocess.Popen('./configer/confclient -p 99 -t Value -g %s' % param, shell=True, stdout = subprocess.PIPE)

def fetch_value_from_configer(cdf_path, prefix_etc_path, param):

	ret = None
	returncode = '' 
	retry = 5
	confclient = None
	configer = None

	configer = start_configer(cdf_path, prefix_etc_path)

	while returncode != 0 and retry != 0:
		confclient = start_confclient(param) 
		confclient.wait()
		returncode = confclient.returncode
		retry = retry - 1
		if retry == 0:
			return None
		#time.sleep(1)

	for out in confclient.stdout: 	
		out = re.sub('\n', '', out)
		ret = out 

        stop_configer(configer)

	return ret
	

# vim: tabstop=8 shiftwidth=8 softtabstop=8 noexpandtab
