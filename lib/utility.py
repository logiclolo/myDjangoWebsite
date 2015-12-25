#!/usr/bin/env python

import sys, os
import re 
import json
import bcolors
import subprocess

flash_base = os.path.join(os.getenv('PRODUCTDIR'), 'flashfs_base')  

def output(filename, content):
	try:
		outh = open(filename,'w')
	except IOError, e:
		print e

	outh.write(content)

def avaiable_model():
	tmp = []
	capability = 'config_capability.xml'

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

			print 'We are ready to update the model: (modify \'%s\' if you want to change models)' % model_file
			print model
			return model


		except IOError, e:
			print e
			sys.exit(1)
	else:
		model = avaiable_model()

		tmp = ''
		for m in model:
			tmp = tmp + m + '\n'

		output(model_file, tmp)

		print bcolors.WARNING + '\'%s\' file does not exist' % model_file + bcolors.NORMAL
		print 'Configurator will update the model CDF/configs according to \'%s\'' % model_file
		print 'We generate the \'%s\' and ready to update the model:' % model_file
		print model
		print bcolors.WARNING + 'You can modify the file and run again' + bcolors.NORMAL

		return model

def strip_model(model):
	tmp = []

	for m in model:
		path = os.path.join(flash_base, m)
		if os.path.isdir(path):
			tmp.append(m)
		else:
			print '%s does not exist. We won\'t update it.' % m

	return tmp



# vim: tabstop=8 shiftwidth=8 softtabstop=8 noexpandtab
