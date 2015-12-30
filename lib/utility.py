#!/usr/bin/env python

import sys, os
import re 
import json
import bcolors
import subprocess


def output(filename, content):
	try:
		outh = open(filename,'w')
	except IOError, e:
		print e

	outh.write(content)

def available_model():
	tmp = []
	capability = 'config_capability.xml'

	flash_base = os.path.join(os.getenv('PRODUCTDIR'), 'flashfs_base')  
	dirs = subprocess.Popen('find %s -iname %s' % (flash_base, capability), shell=True, stdout = subprocess.PIPE).stdout
	for d in dirs: 	
		d = re.sub('\n', '', d)
		m = re.search('.*/([A-Z][A-Z][0-9A-Z]+)/.*', d)
		if m:
			tmp.append(m.group(1))

	return tmp

def choose_model(model_file):
	if os.path.isfile(model_file):
		tmp = []
		try:
			fh = open(model_file, 'r')
			line = fh.readline()

			while line:
				line = re.sub('[\r\n$()]', '', line)
				tmp.append(line)

				line = fh.readline()

			model = strip_model(tmp)

			print 'We are ready to update the model:'
			print model


		except IOError, e:
			print e
			sys.exit(1)
	else:
		model = available_model()

		tmp = ''
		for m in model:
			tmp = tmp + m + '\n'

		output(model_file, tmp)

		print bcolors.WARNING + '\'%s\' file does not exist' % model_file + bcolors.NORMAL
		print 'Configurator will update the model CDF/configs according to \'%s\'' % model_file
		print 'We generate the \'%s\' for you and ready to update the model:' % model_file
		print model


	if len(model) == 0:
		print 'No models. Please modify \'%s\'' % model_file	
		sys.exit(0)

	print bcolors.WARNING
	print 'Modify \'%s\' if you want to change models' % model_file
	print 'Press any key to continue or \'q\' to exit ...'
	print bcolors.NORMAL

	ans = getch()
	if ans == 'q':
		sys.exit(0)

	return model

def strip_model(model):
	tmp = []

	flash_base = os.path.join(os.getenv('PRODUCTDIR'), 'flashfs_base')  
	for m in model:
		path = os.path.join(flash_base, m)
		if os.path.isdir(path):
			tmp.append(m)
		else:
			print bcolors.WARNING + m + bcolors.NORMAL + ' does not exist. We won\'t update it.' 

	return tmp



class _Getch:
    """Gets a single character from standard input.  Does not echo to the screen."""
    def __init__(self):
        try:
            self.impl = _GetchWindows()
        except ImportError:
            self.impl = _GetchUnix()

    def __call__(self): return self.impl()


class _GetchUnix:
    def __init__(self):
        import tty, sys

    def __call__(self):
        import sys, tty, termios
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch


class _GetchWindows:
    def __init__(self):
        import msvcrt

    def __call__(self):
        import msvcrt
        return msvcrt.getch()


getch = _Getch()

# vim: tabstop=8 shiftwidth=8 softtabstop=8 noexpandtab
