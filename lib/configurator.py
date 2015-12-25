#!/usr/bin/env python

import sys, os
import json
import getopt
import os.path
from rule_parser import *
from xml_updater import *

def output(filename, content):
	try:
		outh = open(filename,'w')
	except IOError, e:
		print e

	outh.write(content)

def do_action(action, md, model_matrix):
	obj = md(action, model_matrix)
	ret = obj.action()

	return ret

def action_dispatch(model_matrix):
	for action in model_matrix['action']:
		if action['method'] == 'add':
			do_action(action, add, model_matrix)
		elif action['method'] == 'remove':
			do_action(action, remove, model_matrix)
		elif action['method'] == 'modify':
			do_action(action, modify, model_matrix)


def update_config(matrix):
	for model_matrix in matrix:
		action_dispatch(model_matrix)

def check_envs():
	if not os.getenv('PRODUCTDIR'):
		return False

	return True

def usage():
	usage = 'Usage:%s -v http_api_version' % sys.argv[0] 

	print usage

if __name__ == '__main__':

	opts, args = getopt.getopt(sys.argv[1:], "hv:" )

	#print opts
	for opt, arg in opts:
		if opt in ('-v', ''):
			version = arg 
		if opt in ('-h', ''):
			usage()
			sys.exit(0)

	if len(sys.argv) < 2:
		usage()
		sys.exit(0)

	if not check_envs():
		print 'Have you source the project devel file?'
		sys.exit(1)

	path = './tpl/%s.json' % version

	if not os.path.isfile(path):
		print 'No %s.json found' % version 
		sys.exit(0)

	obj = api_version_object(path) 

	print '#############################################'
	print 'Begin to parse rule.json'
	print '#############################################'
	obj.parse_common_rule()

	print '\n'
	print '#############################################'
	print 'Begin to update CDF/configs'
	print '#############################################'
	obj.parse_api_rule()

	update_config(obj.matrix)


# vim: tabstop=8 shiftwidth=8 softtabstop=8 noexpandtab
