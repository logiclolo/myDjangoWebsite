#!/usr/bin/env python

import sys, os
import re 
import json
from pprint import pprint
from xml.dom import minidom
from lxml import etree
import subprocess
import HTMLParser
from copy import deepcopy

if sys.version_info[:2] >= (2, 5):
	import xml.etree.ElementTree as et 
else:
	import elementtree.ElementTree as et 

debug = True

class base(object):
	# config file path
	conf_path = []
	conf_nmediastream = []

	# xml related
	et_object = None
	et_root = None
	confile = ''
	method = ''
	xpath = ''
	xpaths = []
	cdf_check = ''
	do_list = []

	def __init__(self, action):
		self.confile = action['file']
		self.method = action['method']
		self.locate_config(action)
		self.parse(action)

		print json.dumps(action, indent=4, sort_keys=True)

	def locate_config(self, rule_action):

		tmp = []

		flash_base = os.path.join(os.getenv('PRODUCTDIR'), 'flashfs_base')  
		dirs = subprocess.Popen('find %s -iname %s' % (flash_base, self.confile), shell=True, stdout = subprocess.PIPE).stdout
		for d in dirs: 	
			d = re.sub('\n', '', d)
			tmp.append(d) 

		rule_action['path'] = deepcopy(tmp) #deepcopy is the trick to copy by value

	def fetch_nmediastream(self, rule_element, rule_action):

		capability = 'config_capability.xml'
		xpath = 'capability/nmediastream'

		rule_path = rule_action['path']
		detail = rule_element['detail'] 

		for path in rule_path:
			dirname = os.path.dirname(path)
			caps = subprocess.Popen('find %s -iname %s' % (dirname, capability), shell=True, stdout = subprocess.PIPE).stdout
			for cap in caps:
				cap = re.sub('\n', '', cap)
				et_object = et.parse(cap)
				elem = et_object.find(xpath)
				#self.conf_nmediastream.append(elem.text)

				index = rule_path.index(path)
				detail[index]["s<n>"] = elem.text 

	def gen_param(self, xpath, rule_element, rule_action):

		# find c<n>, s<n> or <..> 
		# and replace the variable with real number/value
		#
		#
		# The final result is saved to rule_action['detail']  
		# and after that self.action() would use these detail

		rule_detail = rule_element['detail']

		prog = re.compile('c<n>')
		patterns = prog.findall(xpath)
		if len(patterns) > 0:
			pattern = patterns[0]

			for de in rule_detail:	
				if len(de['xpath']) == 0:
					value = re.sub(pattern, 'c0', xpath)
					de['xpath'].append(value)

				else:
					tmp = []
					for param in de['xpath']:
						value = re.sub(pattern, 'c0', param)
						tmp.append(value)
					de['xpath'] = deepcopy(tmp)


		prog = re.compile('s<n>')
		patterns1 = prog.findall(xpath)
		self.fetch_nmediastream(rule_element, rule_action)
		if len(patterns1) > 0:
			pattern = patterns1[0]

			for de in rule_detail:	
				if len(de['xpath']) == 0:
					for i in range(0, int(de[pattern])):
						value = re.sub(pattern, 's%d' % i, xpath)
						de['xpath'].append(value)

				else:
					tmp = []
					for param in de['xpath']:
						for i in range(0, int(de[pattern])):
							value = re.sub(pattern, 's%d' % i, param)
							tmp.append(value)
					de['xpath'] = deepcopy(tmp)


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
			print '-----------------------------------------------'

class add(base):
	""" Add the tag into XML """

	parent = ''	
	element = ''
	element_text = ''

	def parse(self, rule_action):

		rule_element = rule_action['element']

		for element in rule_element:
			xpath = element['param']

			# initial a new key as metadata
			detail = element['detail'] = [] 
			tmp = {"xpath":[]}
			for p in rule_action['path']:
				detail.append(deepcopy(tmp))


			m = re.search('<.*>', xpath)
			if m:
				self.gen_param(xpath, element, rule_action)
			else:
				for de in element['detail']:
					de['xpath'].append(xpath)


	def insert_new_node(self, et_object, xpaths, rule_element):

		et_new_node = None
		et_ori_object = et_object

		for xpath in xpaths: 
			# travel every element of the given xpath
			# if the element is not in the xml tree, then insert it
			trace = xpath.split('_')
			for node in trace:	
				ori_object = et_object
				et_object = et_object.find(node)
				if et_object == None:
					et_new_node = et.Element(node)

					if  node == trace[-1]:
						if rule_element.has_key('value'):
							et_new_node.text = rule_element['value'] 
						if rule_element.has_key('check'):
							check = rule_element['check']
							if check != None and check != 'null':
								et_new_check_node = et.Element('check')
								et_new_check_node.text = check 
								et_new_node.append(et_new_check_node)
							et_new_value_node = et.Element('value')
							et_new_node.append(et_new_value_node)


					ori_object.append(et_new_node)
					et_object = ori_object.find(node) 

			et_object = et_ori_object

		return et_new_node


	def action(self, rule_action):

		stain = None
		et_new_node = None

		#self.debug_print()

		paths = rule_action['path']
		elements = rule_action['element']

		for path in paths:
			print path
			et_object = et.parse(path, CommentedTreeBuilder())
			et_root = et_object.getroot()

			for element in elements:
				index = paths.index(path)
				detail = element['detail'][index]
				xpaths = detail['xpath']

				et_new_node = self.insert_new_node(et_object, xpaths, element)	

				if et_new_node != None:
					stain =True

			if stain:
				content = self.prettify(et_root)
				self.output(path, content)
			else:
				print 'The param is already in the %s' % path

		if stain:
			return True 
		else:
			return False 

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
			et_object = et.parse(path, CommentedTreeBuilder())
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
		print 'ready to check cond: %s' % cond
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
					print '%s is match' % task['cond'] 
					self.actions = self.actions + task['action'] 
				else:
					print 'not match'






class CommentedTreeBuilder ( et.XMLTreeBuilder ):
	def __init__ ( self, html = 0, target = None ):
		et.XMLTreeBuilder.__init__( self, html, target )
		self._parser.CommentHandler = self.handle_comment
    
	def handle_comment ( self, data ):
		self._target.start( et.Comment, {} )
		self._target.data( data )
		self._target.end( et.Comment )

# vim: tabstop=8 shiftwidth=8 softtabstop=8 noexpandtab
