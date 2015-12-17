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
from configer import *

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
	xpaths = []
	cdf_check = ''
	do_list = []
	macro = []

	def __init__(self, action, macro):
		self.confile = action['file']
		self.method = action['method']
		self.macro = macro

		self.locate_config(action)
		self.compose_detail(action)

		print json.dumps(action, indent=4, sort_keys=True)

	def locate_config(self, rule_action):

		tmp = []

		flash_base = os.path.join(os.getenv('PRODUCTDIR'), 'flashfs_base')  
		dirs = subprocess.Popen('find %s -iname %s' % (flash_base, self.confile), shell=True, stdout = subprocess.PIPE).stdout
		for d in dirs: 	
			d = re.sub('\n', '', d)
			tmp.append(d) 

		rule_action['path'] = deepcopy(tmp) #deepcopy is the trick to copy by value

	def compose_detail(self, rule_action):

		rule_element = rule_action['element']

		for element in rule_element:
			xpath = element['param']

			# initial 'detail' as metadata
			# which is a list of all the models and each of them contains the real param info
			element['detail'] = self.compose_dict_in_list(rule_action['path'])

			m = re.search('<.*>', xpath)
			if m:
				self.evaluate_param(xpath, element, rule_action)
			else:
				for de in element['detail']:
					de['xpath'].append(xpath)

	def compose_dict_in_list(self, paths):
		listp = []
		dictp = {}
		for path in paths:
			m = re.search('.*/([A-Z][A-Z][0-9A-Z]+)/.*', path)
			if m:
				dictp['model'] = m.group(1)
			else:
				dictp['model'] = None

			dictp['xpath'] = [] 
			dictp['path'] = path
			listp.append(deepcopy(dictp))	

		return deepcopy(listp)


	def evaluate_param(self, xpath, rule_element, rule_action):

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

				else: # 'xpath' is not null 
					tmp = []
					for param in de['xpath']:
						value = re.sub(pattern, 'c0', param)
						tmp.append(value)
					de['xpath'] = deepcopy(tmp)


		prog = re.compile('s<n>')
		patterns1 = prog.findall(xpath)
		self.find_stream_number(rule_element, rule_action)
		if len(patterns1) > 0:
			pattern = patterns1[0]

			for de in rule_detail:	
				if len(de['xpath']) == 0:
					for i in range(0, int(de[pattern])):
						value = re.sub(pattern, 's%d' % i, xpath)
						de['xpath'].append(value)

				else: # 'xpath' is not null 
					tmp = []
					for param in de['xpath']:
						for i in range(0, int(de[pattern])):
							value = re.sub(pattern, 's%d' % i, param)
							tmp.append(value)
					de['xpath'] = deepcopy(tmp)


	def find_stream_number(self, rule_element, rule_action):

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

				index = rule_path.index(path)
				detail[index]["s<n>"] = elem.text 

		# todo: it can use configer to get value too

	def check_cond(self, cond, model):
		macro = self.macro

		m = re.match('(.*)=(.*)', cond)
		if m:
			param = m.group(1)	
			match = m.group(2)
		else:
			param = match = None

		# seach macro
		for mac in macro:
			if model == mac['model']:
				for content in mac['content']:
					if content['name'] == param and content['value'] == match:
						return True
		return False

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

	def find_index(self, target_list, aim):
		for target in target_list:
			if target['path'] == aim:
				return target_list.index(target)

		return None

	def action(self, rule_action):

		stain = False 

		paths = rule_action['path']
		elements = rule_action['element']

		for path in paths:
			print path
			et_object = et.parse(path, CommentedTreeBuilder())
			et_root = et_object.getroot()

			for element in elements:
				index = self.find_index(element['detail'], path) 

				if index != None:
					detail = element['detail'][index]
					xpaths = detail['xpath']
					model = detail['model']
				else:
					continue

				if element.has_key('cond') and not self.check_cond(element['cond'], model): 
					continue

				stain = self.detail_action(et_object, xpaths, element)

			if stain:
				content = self.prettify(et_root)
				self.output(path, content)
			#else:
				#print 'The param is exist or absent. Please check yourself.'

		if stain:
			return True 
		else:
			return False 

	def detail_action(self, et_object, xpaths, rule_element): 
		# overwrite it	

		return None 


class add(base):
	""" Add the tag into XML """

	def detail_action(self, et_object, xpaths, rule_element):
		et_new_node =  self.insert_new_xpath(et_object, xpaths, rule_element)

		if et_new_node != None:
			return True
		else:
			print '\'%s\' exists already !\n' % rule_element['param']
			return False

	def insert_new_xpath(self, et_object, xpaths, rule_element):

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

					# the last element in the xpath may have <check> or <value>
					if  node == trace[-1]:
						if rule_element.has_key('value'):
							value = str(rule_element['value'])
							m = re.match('\?(.*)', value)
							if m:
								# default value
								et_new_node.text = m.group(1) 
								et_comment_node = et.Comment('[Notice] Please modify the default value below !!!')
								ori_object.append(et_comment_node)
							else:
								et_new_node.text = value 

						if rule_element.has_key('check'):
							check = rule_element['check']
							if check != None and check != 'null':
								et_new_check_node = et.Element('check')
								et_new_check_node.text = str(check)
								et_new_node.append(et_new_check_node)
							et_new_value_node = et.Element('value')
							et_new_node.append(et_new_value_node)


					ori_object.append(et_new_node)
					et_object = ori_object.find(node) 

			et_object = et_ori_object

		return et_new_node


class remove(base):
	""" Remove the tag from XML """

	def detail_action(self, et_object, xpaths, rule_element):
		ret =  self.remove_xpath(et_object, xpaths)

		if ret:
			return True
		else:
			print '\'%s\' does not exist !\n' % rule_element['param']
			return False

	def remove_xpath(self, et_object, xpaths):

		ret = False
		for xpath in xpaths: 
			xpath = re.sub('_', '/', xpath)
			m = re.match('(.*)/(.*)$', xpath)
			if m:
				parent = et_object.find(m.group(1))
				child = et_object.find(xpath)
				if parent != None and child != None:
					parent.remove(child)
					ret = True
		return ret



class modify(base):
	""" Modify the XML tag content """

	def detail_action(self, et_object, xpaths, rule_element):
		stain = False

		for xpath in xpaths:
			xpath = re.sub('_', '/', xpath)
			et_target_tag = et_object.find(xpath)

			if et_target_tag is not None:
				et_target_tag.text = str(rule_element['value']) 
				#et_target_tag.set('update', 'yes')
				stain = True

		if not stain:
			print '\'%s\' does not exist !\n' % rule_element['param']

		return stain


class api_version_object(object): 
	version = '' 
	api_rule = ''
	common_rule = ''
	spec_content = [] 
	actions = []
	config_path = []
	macro = [] 

	def __init__(self, path):
		self.api_rule = path
		self.common_rule = 'rule.json'

	def error_msg(self):
		print 'The format of rule is wrong!'
		sys.exit(1)

	def check_cond(self, cond, ques):
		print '[check condition] %s' % cond
		if cond == True:
			return True
		

		# cond in rule.json
		tmp = re.sub("'", "", cond)
		m = re.match('(.*)\sin\s(.*)', tmp)
		if m:
			value = m.group(1) 
			param = m.group(2)



		# cond in api_version.json, eg. 0301c.json
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

	def fetch_models(self):
		# Find numbers of model 
		#
		# Use config_capability.xml to find models, 
		# and save the result in self.macro

		tmp = {} 
		capability = 'config_capability.xml'

		flash_base = os.path.join(os.getenv('PRODUCTDIR'), 'flashfs_base')  
		dirs = subprocess.Popen('find %s -iname %s' % (flash_base, capability), shell=True, stdout = subprocess.PIPE).stdout
		for d in dirs: 	
			d = re.sub('\n', '', d)
			m = re.search('.*/([A-Z][A-Z][0-9A-Z]+)/.*', d)
			if m:
				tmp['model'] = m.group(1) 
			self.macro.append(deepcopy(tmp))


	def check_rule_multiple_cond(self, name, cond, macro):

		ret = False

		split = cond.split('||')
		if len(split) > 1:
			for s in split:
				s = re.sub(' ', '', s)
				ret =  ret | self.check_rule_cond(name, s, macro)
		else:
			ret = self.check_rule_cond(name, cond, macro)

		return ret


	def check_rule_cond(self, name, cond, macro):

		param = ''
		result = ''
		model = macro['model']

		tmp = re.sub("'", "", cond)

		m = re.match('(.*)\sin\s(.*)', tmp)
		if m:
			match = m.group(1)
			param = m.group(2)	
			

		m = re.match('(.*)=(.*)', tmp)
		if m:
			param = m.group(1)	
			match = m.group(2)


		flash_base = os.path.join(os.getenv('PRODUCTDIR'), 'flashfs_base')  
		cdf_path = os.path.join(flash_base, model, 'etc', 'CDF.xml')
		prefix_etc_path = os.path.join(flash_base, model)

		value = fetch_value_from_configer(cdf_path, prefix_etc_path, param)

		if debug:
			print '---------------------------------'
			print cdf_path
			print prefix_etc_path
			print model 
			print 'name:%s' % name
			print 'param:%s' % param 
			print 'value:%s' % value 
			print 'match:%s' % match 
			print '---------------------------------'


		# if the value is None, it means that the param is not maintained by configer
		# it would be CAMERA_MODEL, CAMERA_TYPE... 
		if value == None:
			for m in macro['content']:
				if m['name'] == param and m['value'] == match:
					return True
					

		if match == value:
			return True
		elif value != None and match in value:
			return True
		else:
			return False


	def handle_detail_common_rule(self, macro, content, index):

		rules = content['rule']
		name = content['param']

		for rule in rules:

			if debug:
				print '\n'

			m = self.check_rule_multiple_cond(name, rule['cond'], macro)
			if m:
				macro['content'][index]['value'] = rule['value']
				if debug:
					print json.dumps(macro, indent=4, sort_keys=True)
				break

	def compose_dict_in_list(self, names):
		listp = []
		dictp = {}
		for name in names:
			dictp['name'] = name 
			dictp['value'] = None
			listp.append(deepcopy(dictp))	

		return deepcopy(listp)

	def parse_common_rule(self):
		data = open(self.common_rule).read()  
		jdata = json.loads(data)

		if not jdata.has_key('name') and not jdata.has_key('content'):
			error_msg()

		# following is composing the self.macro 
		# which contains all the information we need 

		self.fetch_models()

		for m in self.macro:
			m['content'] = self.compose_dict_in_list(jdata['name'])
			for content in jdata['content']:
				# the index is for self.macro[model]['content'][index]
				# and it would be used after the condition is matched
				index = jdata['content'].index(content)

				self.handle_detail_common_rule(m, content, index)


		print json.dumps(self.macro, indent=4, sort_keys=True)

	def parse_api_rule(self):
		data = open(self.api_rule).read()  
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
