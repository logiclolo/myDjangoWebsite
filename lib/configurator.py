#!/usr/bin/env python

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

def action_dispatch(matrix):
	for action in matrix['action']:
		Dispatcher(action, matrix)

def update_config(matrix):
	for m in matrix:
		configer = Configer(m['model'])
		m['configer'] = configer

		print bcolors.BLUE + 'handle %s ...' % m['model'] + bcolors.NORMAL
		action_dispatch(m)

		configer.stop()

def check_envs():
	if not os.getenv('PRODUCTDIR'):
		return False

	return True

def usage():
	usage = 'Usage: %s [-a version] [-f]\
		\n\t-a\tSpecify a  http_api_version\
		\n\t-f\tFormat the CDF/configs' % sys.argv[0]   

	print usage

if __name__ == '__main__':
	
	version = ''
	opts, args = getopt.getopt(sys.argv[1:], "hfa:" )

	#print opts
	for opt, arg in opts:
		if opt in ('-a', ''):
			version = arg 
		if opt in ('-f', ''):
			config.g_format = True
		if opt in ('-h', ''):
			usage()
			sys.exit(0)

	if len(sys.argv) < 2:
		usage()
		sys.exit(0)

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

	model = choose_model('model-list')

	obj = RuleParser(path, model)

	if not config.g_format:
		tmp = obj.check_file_well_formed()

		if len(tmp) > 0:
			print bcolors.WARNING
			print 'The following CDF or configs is not a well-formed xml:' + bcolors.NORMAL
			pp = pprint.PrettyPrinter()
			pp.pprint(tmp)
			print '------------------------------------------------------------------------------------------------------------'
			print 'Strongly recommend you to format it first with executing \"configurator -a xxx -f\" and commit the change'
			print 'if not, the xml after update would contain the unnecessary format change information which bothers you'
			print '------------------------------------------------------------------------------------------------------------'
			print 'Press any key to continue or \'q\' to exit ...'

			ans = getch()
			if ans == 'q':
				sys.exit(0)

	print '####################################################'
	print 'Parsing rule.json ...'
	print '####################################################'
	obj.parse_common_rule()

	print '####################################################'
	print 'Parsing %s.json ...' % version
	print '####################################################'
	obj.parse_api_rule()

	update_config(obj.matrix)


# vim: tabstop=8 shiftwidth=8 softtabstop=8 noexpandtab
