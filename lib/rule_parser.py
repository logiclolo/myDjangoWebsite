#!/usr/bin/env python

import sys, os
import re 
import json
from pprint import pprint
from xml.dom import minidom
from lxml import etree
import subprocess
import HTMLParser

if sys.version_info[:2] >= (2, 5):
	import xml.etree.ElementTree as et 
else:
	import elementtree.ElementTree as et 

debug = True

class base(object):
	# config file path
	conf_path = []

	# xml related
	et_object = None
	et_root = None
	confile = ''
	method = ''
	xpath = ''
	cdf_check = ''

	def __init__(self, action):
		self.confile = action['file']
		self.method = action['method']
		#self.et_object = et.parse(action['file'])
		#self.et_root = self.et_object.getroot()
		self.conf_path = self.locate_config()

		print("\n".join(self.conf_path))

	def locate_config(self):

		tmp = []

		flash_base = os.path.join(os.getenv('PRODUCTDIR'), 'flashfs_base')  
		dirs = subprocess.Popen('find %s -iname %s' % (flash_base, self.confile), shell=True, stdout = subprocess.PIPE).stdout
		for d in dirs: 	
			d = re.sub('\n', '', d)
			tmp.append(d)

		return tmp

	def prettify(self, elem):
		"""Return a pretty-printed XML string for the Element."""
		rough_string = et.tostring(elem, 'utf-8')
		reparsed = minidom.parseString(rough_string)
		tmp = reparsed.toprettyxml(indent="\t")
		
		# remove the redundant line
		xml_content = re.sub('(\t+\s*\n+)+', '', tmp) 
		#xml_content = re.sub('^<?.*?>\n', '', xml_content)

		# handle the escape
		# eg. &quot, &lt, &gt
		h = HTMLParser.HTMLParser()
		xml_content = h.unescape(xml_content)

		return xml_content 

	def output(self, filename, content):
		try:
			outh = open(filename,'w')
		except IOError, e:
			print e

		outh.write(content)

	def debug_print(self):

		if debug:
			print '\n'
			print '-----------------------------------------------'
			print 'action: %s' % self.method
			print 'param: %s' % self.xpath
			print 'confiles:'
			print ("\n".join(self.conf_path))
			print '-----------------------------------------------'

class add(base):
	""" Add the tag into XML """

	parent = ''	
	element = ''
	element_text = ''

	def parse(self, rule):

		xpath = rule['param']
		self.xpath = xpath

		m = re.search('<.*>', xpath)
		if m:
			print 'Has < or > in xpath'
		else:
			m = re.match('(.*)_(.*)$', xpath)
			if m:
				self.parent = m.group(1)
				self.element = m.group(2)

			if rule.has_key('value'):
				self.element_text = rule['value']
			else:
				self.element_text = ''

		if rule.has_key('check'): 
			self.cdf_check = rule['check']
		else:
			self.cdf_check = ''


	def action(self):

		stain = None
		et_new_node = None
		xpath = self.xpath

		if not xpath:
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


		for path in self.conf_path:
			et_object = et.parse(path, CommentedTreeBuilder())
			et_root = et_object.getroot()

			# travel every element of the given xpath
			# if the element is not in the xml tree, then insert it
			trace = xpath.split('_')
			for node in trace:	
				ori_object = et_object
				et_object = et_object.find(node)
				if et_object == None:
					et_new_node = et.Element(node)

					if  node == trace[-1]:
						et_new_node.text = self.element_text
						if self.cdf_check != '':
							if self.cdf_check != 'null':
								et_new_check_node = et.Element('check')
								et_new_check_node.text = self.cdf_check 
								et_new_node.append(et_new_check_node)
							et_new_value_node = et.Element('value')
							et_new_node.append(et_new_value_node)


					ori_object.append(et_new_node)
					et_object = ori_object.find(node) 

			if et_new_node is not None:
				content = self.prettify(et_root)
				self.output(path, content)
				et_new_node = None
			else:
				print 'The param is already in the %s' % path
				stain = True

		if stain:
			return False
		else:
			return True

class remove(base):
	""" Remove the tag from XML """

	parent = ''
	element = '' 

	def parse(self, rule):

		xpath = rule['param']
		self.xpath = xpath

		m = re.search('<.*>', xpath)
		if m:
			print 'Has < or > in xpath'
		else:
			m = re.match('(.*)_(.*)$', xpath)
			if m:
				self.parent = m.group(1)
				self.element = m.group(2)

		if rule.has_key('check'): 
			self.cdf_check = rule['check']
		else:
			self.cdf_check = ''

	def action(self):

		stain = False

		xpath = self.xpath
		if not xpath:
			print 'Please assign xpath for remove first!'
			sys.exit(1)

		self.debug_print()

		et_object = self.et_object

		for path in self.conf_path:
			et_object = et.parse(path)
			et_root = et_object.getroot()

			xpath = re.sub('_', '/', self.xpath)
			elem = et_object.find(xpath)
			if elem is not None:
				xpath = re.sub('_', '/', self.parent)
				parent = et_object.find(xpath)
				xpath = re.sub('_', '/', self.xpath)
				child = et_object.find(xpath)
				parent.remove(child)

				content = self.prettify(et_root)
				self.output(path, content)
			else:
				stain = True
				print 'There is no such param in %s' % path 

		if stain:
			return False
		else:
			return True

class modify(base):
	""" Modify the XML tag content """

	element_text = ''

	def parse(self, rule):
		xpath = rule['param']
		
		m = re.search('<.*>', xpath)
		if m:
			print 'Has < or > in xpath'
		else:
			self.xpath = xpath
			self.element_text = rule['value']

		if rule.has_key('check'): 
			self.cdf_check = rule['check']
		else:
			self.cdf_check = ''

	def action(self):

		stain = False

		xpath = self.xpath
		if not xpath:
			print 'Please assign xpath for remove first!'
			sys.exit(1)

		self.debug_print()

		for path in self.conf_path:
			et_object = et.parse(path, CommentedTreeBuilder())
			et_root = et_object.getroot()
			xpath = re.sub('_', '/', xpath)

			et_target_tag = et_object.find(xpath)

			if et_target_tag is not None:
				et_target_tag.text = self.element_text 
				#et_target_tag.set('update', 'yes')

				content = self.prettify(et_root)
				self.output(path, content)
			else:
				stain = True
				print 'There is no such param in %s' % path 

		if stain:
			return False
		else:
			return True


class api_version_object(object): 
	version = '' 
	path = ''
	spec_content = [] 
	actions = []
	config_path = []

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

	def locate_config(self):
		actions = self.actions

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






class CommentedTreeBuilder ( et.XMLTreeBuilder ):
    def __init__ ( self, html = 0, target = None ):
        et.XMLTreeBuilder.__init__( self, html, target )
        self._parser.CommentHandler = self.handle_comment
    
    def handle_comment ( self, data ):
        self._target.start( et.Comment, {} )
        self._target.data( data )
        self._target.end( et.Comment )
# vim: tabstop=8 shiftwidth=8 softtabstop=8 noexpandtab
