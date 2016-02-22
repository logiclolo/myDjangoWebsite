#!/usr/bin/env python
#encoding: utf-8

import sys, os
import json
import getopt
import os.path
import pprint
from rule_parser import *
from xml_updater import *
from utility import *
from action_dispatcher import *
import config
import atexit
import tempfile
from progress_bar import *

def action_dispatch(matrix):
	# spinning indicator
	print 'handling ...'
	(number, tmp_file) = tempfile.mkstemp()
	example = ThreadingSpinning(tmp_file)

	for action in matrix['action']:
		Dispatcher(action, matrix)

	os.remove(tmp_file)

def update_config(obj):
	matrix = obj.matrix

	for m in matrix:
		apis = m['update']
		model = m['model']

		print bcolors.GOOD
		print '############################'
		print 'Handle %s ...' % model
		print '############################' + bcolors.NORMAL

		configer = Configer(model)
		m['configer'] = configer
		config.g_configer = configer

		for api in apis:
			obj.parse_api_rule(api, model)
			action_dispatch(m)

			# print results
			if config.g_format:	
				print '\nFormating ...'
				pp = pprint.PrettyPrinter()
				pp.pprint(config.g_format_list)
			else:
				xml_update_err_show()	

		if len(apis) == 0:
			print 'api is up to date'

		configer.stop()

def check_envs():
	if not os.getenv('PRODUCTDIR'):
		return False

	return True

def release():
	remove_flashfs_tmp()
	if config.g_configer is not None:
		config.g_configer.stop()

def usage():
	usage = 'Usage: %s [-a version] [-f version]\
		\n\t-a\tSpecify a http_api_version to update\
		\n\t-f\tSpecify a http_api_version to format\
		\n\t-l\tList all http_api_version'\
		% sys.argv[0]   

	print usage

if __name__ == '__main__':
	
	version = ''
	opts, args = getopt.getopt(sys.argv[1:], "hla:f:" )

	#print opts
	for opt, arg in opts:
		if opt in ('-a', ''):
			version = arg 
		if opt in ('-f', ''):
			config.g_format = True
			version = arg 
		if opt in ('-l', ''):
			show_all_api()
			sys.exit(0)
		if opt in ('-h', ''):
			usage()
			sys.exit(0)

	if len(sys.argv) < 2:
		usage()
		sys.exit(0)

	atexit.register(release)

	if version == '':
		print 'Please specify a http_api_version'
		sys.exit(0)

	if not check_envs():
		print 'Have you source the project devel file?'
		sys.exit(1)

	path = './api/%s.json' % version
	if not os.path.isfile(path):
		print 'No %s.json found' % version
		sys.exit(0)
	
	models = choose_model('model-list')
	copy_flashfs_base_to_tmp(models)

	obj = RuleParser(path, models)
	obj.parse_common_rule()


	# We still need to check the format of configs
	# even if user does not specify format
	if not config.g_format:
		check_file_format(obj)

	update_config(obj)
	copy_tmp_to_flashfs_base()

# vim: tabstop=8 shiftwidth=8 softtabstop=8 noexpandtab
