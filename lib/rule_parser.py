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

debug = True

class base(object):
	et_object = None
	et_root = None
	confile = ''
	method = ''
	path = ''

	def __init__(self, action):
		self.confile = action['file']
		self.method = action['method']
		self.et_object = et.parse(action['file'])
		self.et_root = self.et_object.getroot()


	def debug_print(self):

		if debug:
			print '-----------------------------------------------'
			print 'confile: %s' % self.confile
			print 'action: %s' % self.method
			print 'param: %s' % self.path
			print '-----------------------------------------------'

class add(base):
	""" Add the tag into XML """

	parent = ''	
	element = ''
	element_text = ''

	def parse(self, rule):

		path = rule['param']
		self.path = path

		m = re.search('<.*>', path)
		if m:
			print 'Has < or > in path'
		else:
			m = re.match('(.*)_(.*)$', path)
			if m:
				self.parent = m.group(1)
				self.element = m.group(2)

			self.element_text = rule['value']


	def action(self):

		et_new_node = None
		path = self.path

		if not path:
			print 'Please assign xpath for add first!'
			sys.exit(1)

		self.debug_print()

		#et_object = self.et_object
		#xpath = re.sub('_', '/', self.parent)
		#parent = et_object.find(xpath)
		#child = et.Element(self.element)
		#child.text = self.element_text
		#parent.append(child)
		#return True


		# travel every element of the given xpath
		# if the element is not in the xml tree, then insert it
		et_object = self.et_object
		trace = path.split('_')
		for node in trace:	
			ori_object = et_object
			et_object = et_object.find(node)
			if et_object == None:
				et_new_node = et.Element(node)

				if  node == trace[-1]:
					et_new_node.text = self.element_text

				ori_object.append(et_new_node)
				et_object = ori_object.find(node) 

		if et_new_node:
			return True 
		else:
			return False 

class remove(base):
	""" Remove the tag from XML """

	parent = ''
	element = '' 

	def parse(self, rule):

		path = rule['param']
		self.path = path

		m = re.search('<.*>', path)
		if m:
			print 'Has < or > in path'
		else:
			m = re.match('(.*)_(.*)$', path)
			if m:
				self.parent = m.group(1)
				self.element = m.group(2)

	def action(self):
		path = self.path

		if not path:
			print 'Please assign xpath for remove first!'
			sys.exit(1)

		self.debug_print()

		et_object = self.et_object

		xpath = re.sub('_', '/', self.parent)
		parent = et_object.find(xpath)
		xpath = re.sub('_', '/', self.path)
		child = et_object.find(xpath)

		parent.remove(child)

		return True

		#et_object = self.et_object
		#trace = path.split('_')
		#for node in trace:	
			## we must find the parent and then remove its child
			#et_object_parent = et_object
			#et_object = et_object.find(node)
			#if et_object == None:
				#return False	

		#et_object_parent.remove(et_object)
		#return True

class modify(base):
	""" Modify the XML tag content """

	element_text = ''

	def parse(self, rule):
		path = rule['param']
		
		m = re.search('<.*>', path)
		if m:
			print 'Has < or > in path'
		else:
			self.path = path
			self.element_text = rule['value']

	def action(self):
		path = self.path

		if not path:
			print 'Please assign xpath for remove first!'
			sys.exit(1)

		self.debug_print()

		et_object = self.et_object
		xpath = re.sub('_', '/', path)

		et_target_tag = et_object.find(xpath)
		et_target_tag.text = self.element_text 
		#et_target_tag.set('update', 'yes')

		return True


class api_version_object(object): 
	version = '' 
	path = ''
	spec_content = [] 
	actions = []

	def __init__(self, path):
		self.path = path

	def error_msg(self):
		print 'The format of rule is wrong!'
		sys.exit(1)

	def check_cond(self, cond, ques):
		print '### ready to check cond: %s' % cond
		if cond == True:
			return True
		
		m = re.match('qid\[(.*)\].*=(.*)', cond)
		if ques != None and m:
			#print m.group(1)
			#print m.group(2)
			for q in ques:
				if q['id'] == int(m.group(1)) and q['ans'] == m.group(2):
					return True
					

		return False

	def check_answer(self, ques, ans):

		try:
			ans_num = int(ans)
		except ValueError:
			print 'Please give an integer.'
			return False

		# find the numbers of question selection
		prog = re.compile('\([0-9]*\)')
		result = prog.findall(ques)
		sel_num = len(result)

		if sel_num == 0:
			return True
		if ans_num > 0 and ans_num <= sel_num:
			return True
		else:
			print 'Wrong selection. Please input again.'
			return False
		

	def ask_user(self, question):
		if self.check_cond(question['cond'], None):
			ques = question['ask']

			print ques 
			ans = raw_input()
			while not self.check_answer(ques, ans):
				ans = raw_input()
			
			question['ans'] = ans


	def parse_rule(self):
		data = open(self.path).read()  
		jdata = json.loads(data)

		if not jdata.has_key('version') and not jdata.has_key('content'):
			error_msg()

		self.version = jdata['version']
		content = jdata['content']
		specs = jdata['content']['spec']
		self.spec_content = specs

		for spec in specs:
			questions = spec['ques']
			tasks = spec['task']
			#print spec['type']

			for question in questions: 
				self.ask_user(question)
				#print question['ans']

			for task in tasks: 
				if self.check_cond(task['cond'], questions):
					print '%s is match!!!!!!' % task['cond'] 
					self.actions = self.actions + task['action'] 






# vim: tabstop=8 shiftwidth=8 softtabstop=8 noexpandtab
