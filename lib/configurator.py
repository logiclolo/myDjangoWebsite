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

def prettify(elem):
	"""Return a pretty-printed XML string for the Element."""
	rough_string = et.tostring(elem, 'utf-8')
	reparsed = minidom.parseString(rough_string)
	tmp = reparsed.toprettyxml(indent="\t")
	
	# remove the redundant line
	xml_content = re.sub('(\t+\n+)+', '', tmp) 
	xml_content = re.sub('^<?.*?>\n', '', xml_content)
	return xml_content 

def error_msg():
	print 'The format of rule is wrong!'
	sys.exit(1)

def check_rule_condition(cond, jdata):
	if cond == None: 
		return True

	subcond = cond.split('&')
	for c in subcond:
		print c
		m = re.search('question[(.*)].*=()', c)
		if m:
			print m.group(0)
			print m.group(1)

def parse_rule(jdata):
	#pprint (jdata)

	if not jdata.has_key('content'):
		error_msg()
	#if jdata.has_key('question'):
		#questions = jdata['content']['question']
		#for question in questions:
			#if isinstance(question, dict):
				#print 'dict'
				#cond = question['cond']
			#elif isinstance(question, list):
				#print 'list'
				#for q in question:
					#cond = q['cond']

def upgrade_config(configs, actions):

	for f in configs:
		et_object = et.parse(f)
		et_root = et_object.getroot()

		#et_object = etree.parse(f)
		#et_root = et_object.getroot()
		#et_root.append(etree.Element('logic'))


		for key, value in sorted(command.iteritems()):
			print key
			print value
			print value['action']

		remove().action(et_object, rule['xpath'])
		modify().action(et_object, rule1['xpath'], rule1['text'])
		add().action(et_object, rule2['parentxpath'], rule2['tag'], rule2['text'])

		content = prettify(et_root)
		output(f, content)
		#et_object.write(f)

def action_dispatch(action, md):
	confile = action['file']
	doing_list = action['element']

	print action
	obj = md(action)

	for do in doing_list:
		obj.parse(do)
		ret = obj.action()
		if ret:
			print 'Modify successfully!\n'
		else:
			print 'The config file may already contain the update you want!\n'


	content = prettify(obj.et_root)
	output(confile, content)	

def update_config(actions):

	for action in actions:
		if action['method'] == 'add':
			action_dispatch(action, add)
		elif action['method'] == 'remove':
			action_dispatch(action, remove)
		elif action['method'] == 'modify':
			action_dispatch(action, modify)

if __name__ == '__main__':
	obj = api_version_object('test.json') 
	obj.parse_rule()
	print obj.actions

	update_config(obj.actions)


	#data = open('0301c.json').read()
	#jdata = json.loads(data)
	#parse_rule(jdata)
	#upgrade_config()



# vim: tabstop=8 shiftwidth=8 softtabstop=8 noexpandtab
