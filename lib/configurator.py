#!/usr/bin/env python

import sys, os
import re 
import json
from pprint import pprint
from xml.dom import minidom
from lxml import etree
from rule_parser import *

if sys.version_info[:2] >= (2, 5):
	import xml.etree.ElementTree as et 
else:
	import elementtree.ElementTree as et 

def output(filename, content):
	try:
		outh = open(filename,'w')
	except IOError, e:
		print e

	outh.write(content)

def action_dispatch(action, md):
	confile = action['file']
	doing_list = action['element']

	obj = md(action)

	for do in doing_list:
		obj.parse(do)
		ret = obj.action()
		if ret:
			print 'Modify successfully!\n'


def update_config(actions):

	for action in actions:
		if action['method'] == 'add':
			action_dispatch(action, add)
		elif action['method'] == 'remove':
			action_dispatch(action, remove)
		elif action['method'] == 'modify':
			action_dispatch(action, modify)

def check_envs():
	if not os.getenv('PRODUCTDIR'):
		return False

	return True

if __name__ == '__main__':


	if not check_envs():
		print 'Have you source the project devel file?'
		sys.exit(1)

	obj = api_version_object('test.json') 
	obj.parse_rule()

	update_config(obj.actions)


# vim: tabstop=8 shiftwidth=8 softtabstop=8 noexpandtab
