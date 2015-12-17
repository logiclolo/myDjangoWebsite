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

def action_dispatch(action, md, macro):
	obj = md(action, macro)
	ret = obj.action(action)
	if ret:
		print 'Modify successfully!\n'

def update_config(actions, macro):

	for action in actions:
		if action['method'] == 'add':
			action_dispatch(action, add, macro)
		elif action['method'] == 'remove':
			action_dispatch(action, remove, macro)
		elif action['method'] == 'modify':
			action_dispatch(action, modify, macro)

def check_envs():
	if not os.getenv('PRODUCTDIR'):
		return False

	return True

if __name__ == '__main__':


	if not check_envs():
		print 'Have you source the project devel file?'
		sys.exit(1)

	obj = api_version_object('0301c.json') 
	obj.parse_common_rule()
	obj.parse_api_rule()

	update_config(obj.actions, obj.macro)


# vim: tabstop=8 shiftwidth=8 softtabstop=8 noexpandtab
