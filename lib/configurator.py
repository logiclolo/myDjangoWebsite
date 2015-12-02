#!/usr/bin/env python

import sys, os
import re 
import json
from pprint import pprint
from xml.dom import minidom
from lxml import etree

if sys.version_info[:2] >= (2, 5):
	import xml.etree.ElementTree as et 
else:
	import elementtree.ElementTree as et 



class add(object):
	""" Add the tag into XML """

	def action(self, et_object, parent, tag, text):
		et_ori_object = et_object
		trace = parent.split('/')
		for node in trace:	
			et_object = et_object.find(node)
			if et_object == None:
				return False

		et_new_node = et.Element(tag)
		et_new_node.text = text 
		et_object.append(et_new_node)
		#et_object.insert(1, et_new_node)

		return True

class remove(object):
	""" Remove the tag from XML """

	def action(self, et_object, xpath):
		trace = xpath.split('/')
		for node in trace:	
			# we must find the parent and then remove its child
			et_object_parent = et_object
			et_object = et_object.find(node)
			if et_object == None:
				return False	

		et_object_parent.remove(et_object)
		return True
		

class modify(object):
	""" Modify the XML tag content """

	def action(self, et_object, xpath, text):
		et_target_tag = et_object.find(xpath)
		et_target_tag.text = text 
		#et_target_tag.set('update', 'yes')

		return True

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

def ask_user(question, jdata, q_index):
	while True:
		print question

		and = raw_input()
	

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

	if jdata.has_key('content'):
		questions = jdata['content']['question']
		for q in questions:
			if check_rule_condition(q['cond'], jdata):
				

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

def upgrade_config(configs):

	sys.exit(0)

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


if __name__ == '__main__':

	data = open('0301c.json').read()
	jdata = json.loads(data)
	parse_rule(jdata)
	#upgrade_config()



# vim: tabstop=8 shiftwidth=8 softtabstop=8 noexpandtab
