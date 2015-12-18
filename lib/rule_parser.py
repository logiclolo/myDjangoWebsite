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
	confile = ''
	method = ''
	matrix_action = {} 
	matrix_contents = []
	matrix_model = ''

	def __init__(self, action, matrix):
		self.confile = action['file']
		self.method = action['method']
		self.matrix_action = action
		self.matrix_contents = matrix['content'] 
		self.matrix_model = matrix['model'] 

		self.locate_config()
		self.compose_detail_action()

		print json.dumps(self.matrix_action, indent=4, sort_keys=True)

	def locate_config(self):

		self.matrix_action['path'] = '' 

		directory = os.path.join(os.getenv('PRODUCTDIR'), 'flashfs_base', self.matrix_model)  
		path = subprocess.Popen('find %s -iname %s' % (directory, self.confile), shell=True, stdout = subprocess.PIPE).stdout
		for p in path: 	
			p = re.sub('\n', '', p)
			self.matrix_action['path'] = p

		# the file could be in 'common'
		if len(self.matrix_action['path']) == 0:
			flash_base = os.path.join(os.getenv('PRODUCTDIR'), 'flashfs_base', 'common')
			path = subprocess.Popen('find %s -iname %s' % (flash_base, self.confile), shell=True, stdout = subprocess.PIPE).stdout
			for p in path: 	
				p = re.sub('\n', '', p)
				self.matrix_action['path'] = p


	def compose_detail_action(self):

		elements = self.matrix_action['element'] 

		for element in elements:
			xpath = element['param']
			m = re.search('<.*>', xpath)
			if m:
				self.evaluate_param(element)
			else:
				for de in element['detail']:
					de['xpath'].append(xpath)

	def evaluate_param(self, element):

		# find c<n>, s<n> or <..> 
		# and replace the variable with real number/value
		#
		#
		# The final result is saved to element['xpath']  
		# and after that self.action() would use these detail

		element['xpath'] = [] 
		element['xpath'].append(deepcopy(element['param']))

		prog = re.compile('c<n>')
		patterns = prog.findall(element['param'])
		if len(patterns) > 0:
			pattern = patterns[0]

			tmp = []
			for x in element['xpath']:
				value = re.sub(pattern, 'c0', x)
				tmp.append(value)
			element['xpath'] = deepcopy(tmp)


		prog = re.compile('s<n>')
		patterns = prog.findall(element['param'])
		if len(patterns) > 0:
			self.find_stream_number(element)
			pattern = patterns[0]

			number = int(element[pattern]) 
			tmp = []
			for x in element['xpath']:
				for i in range(0, number):
					value = re.sub(pattern, 's%d' % i, x)
					tmp.append(value)
			element['xpath'] = deepcopy(tmp)


	def find_stream_number(self, element):

		capability = 'config_capability.xml'
		xpath = 'capability/nmediastream'

		path = self.matrix_action['path']
		dirname = os.path.dirname(path)
		caps = subprocess.Popen('find %s -iname %s' % (dirname, capability), shell=True, stdout = subprocess.PIPE).stdout
		for cap in caps:
			cap = re.sub('\n', '', cap)
			et_object = et.parse(cap)
			elem = et_object.find(xpath)

			element['s<n>'] = elem.text

		# todo: it can use configer to get value too


	def check_cond(self, cond):

		m = re.match('(.*)=(.*)', cond)
		if m:
			param = m.group(1)	
			match = m.group(2)
		else:
			param = match = None

		for content in self.matrix_contents:
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

	def action(self):

		stain = False 

		path = self.matrix_action['path']
		elements = self.matrix_action['element']

		if path != '':
			print path
			et_object = et.parse(path, CommentedTreeBuilder())
			et_root = et_object.getroot()
		else:
			return False


		for element in elements:
			if element.has_key('cond') and not self.check_cond(element['cond']): 
				continue

			stain = self.detail_action(et_object, element)

		if stain:
			content = self.prettify(et_root)
			self.output(path, content)
		#else:
			#print 'The param is exist or absent. Please check yourself.'

		if stain:
			return True 
		else:
			return False 


	def detail_action(self, et_object, xpaths, element): 
		# overwrite it	

		return None 


class add(base):
	""" Add the tag into XML """

	def detail_action(self, et_object, element):
		et_new_node =  self.insert_new_xpath(et_object, element)

		if et_new_node != None:
			return True
		else:
			print '\'%s\' exists already !\n' % element['param']
			return False

	def insert_new_xpath(self, et_object, element):

		et_new_node = None
		et_ori_object = et_object
		xpaths = element['xpath']

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
						if element.has_key('value'):
							value = str(element['value'])
							m = re.match('\?(.*)', value)
							if m:
								# default value
								et_new_node.text = m.group(1) 
								et_comment_node = et.Comment('[Notice] Please modify the default value below !!!')
								ori_object.append(et_comment_node)
							else:
								et_new_node.text = value 

						if element.has_key('check'):
							check = element['check']
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

	def detail_action(self, et_object, element):
		ret =  self.remove_xpath(et_object, element)

		if ret:
			return True
		else:
			print '\'%s\' does not exist !\n' % element['param']
			return False

	def remove_xpath(self, et_object, element):

		ret = False
		xpaths = element['xpath']

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

	def detail_action(self, et_object, element):
		stain = False

		xpaths = element['xpath']

		for xpath in xpaths:
			xpath = re.sub('_', '/', xpath)
			et_target_tag = et_object.find(xpath)

			if et_target_tag is not None:

				if element.has_key('value'):
					et_target_tag.text = str(element['value']) 

				if element.has_key('check'):
					et_child_tag = et_target_tag.find('check')
					if et_child_tag != None: 
						et_child_tag.text = str(element['check'])

				#et_target_tag.set('update', 'yes')
				stain = True

		if not stain:
			print '\'%s\' does not exist !\n' % element['param']

		return stain


class api_version_object(object): 
	version = '' 
	api_rule = ''
	common_rule = ''
	actions = []
	config_path = []
	matrix = [] 

	def __init__(self, path):
		self.api_rule = path
		self.common_rule = 'rule.json'

		self.initial_matrix()

	def error_msg(self):
		print 'The format of rule is wrong!'
		sys.exit(1)

	def check_cond1(self, cond, ques, content):
		#print '[check condition] %s' % cond
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
		

	def ask_user(self, question, matrix):
		if self.check_cond(question['cond'], matrix):
			ques = question['ask']

			print '\nPlease answer the questions based on \'%s\' ...' % model
			print ques 
			ans = raw_input()
			while not self.check_answer(ques, ans):
				ans = raw_input()
			
			#question['ans'] = ans
			qid = question['id']
			matrix['answer'][qid] = ans
		else:
			print 'don\'t need to ask.'

	def initial_matrix(self):

		# The matrix contains the main infomation that we need
		# and note that the length of matrix is 'numbers of model'
		#
		# (1) Find numbers of model 
		# Use config_capability.xml to find models, 
		#
		# (2) action list
		# We initial the list first and it would be assigned after

		tmp = {} 
		capability = 'config_capability.xml'

		flash_base = os.path.join(os.getenv('PRODUCTDIR'), 'flashfs_base')  
		dirs = subprocess.Popen('find %s -iname %s' % (flash_base, capability), shell=True, stdout = subprocess.PIPE).stdout
		for d in dirs: 	
			d = re.sub('\n', '', d)
			m = re.search('.*/([A-Z][A-Z][0-9A-Z]+)/.*', d)
			if m:
				tmp['model'] = m.group(1) 

			tmp['action'] = [] 
			tmp['content'] = [] 
			tmp['answer'] = []
			self.matrix.append(deepcopy(tmp))

	def check_cond(self, cond, matrix):

		ret = False

		split = cond.split('||')
		if len(split) > 1:
			for s in split:
				s = re.sub(' ', '', s)
				ret =  ret | self.check_detail_cond(s, matrix)
		else:
			ret = self.check_detail_cond(cond, matrix)

		return ret


	def check_detail_cond(self, cond, matrix):

		param = ''
		match = ''
		model = matrix['model']

		flag = True 
		value = None

		tmp = re.sub("'", "", cond)

		if cond == True or cond == 'true':
			if debug:
				print '\n------------ cond_check() ---------------'
				print 'cond: %s' % cond
				print '-----------------------------------------'
			return True


		# ex: qid[1].val=1
		m = re.match('qid\[(.*)\].*=(.*)', cond)
		if m:
			answer = matrix['answer']
			qid = int(m.group(1))
			match = m.group(2)
			if len(answer) >= qid and answer[qid] == match: 
				return True
			else:
				return False
				

		# ex: 'FD' in 'system_info_extendedmodelname'
		m = re.match('(.*)\sin\s(.*)', tmp)
		if m:
			match = m.group(1)
			param = m.group(2)	
			

		# CAMERA_TYPE!=VC
		m = re.match('(.*)!=(.*)', tmp)
		if m:
			flag = False 
			param = m.group(1)	
			match = m.group(2)

		# capability_fisheye=1
		m = re.match('(^!)=(^!)', tmp)
		if m:
			param = m.group(1)	
			match = m.group(2)


		if param != '':
			flash_base = os.path.join(os.getenv('PRODUCTDIR'), 'flashfs_base')  
			cdf_path = os.path.join(flash_base, model, 'etc', 'CDF.xml')
			prefix_etc_path = os.path.join(flash_base, model)

			value = fetch_value_from_configer(cdf_path, prefix_etc_path, param)



		# if the value is None, it means that the param is not maintained by configer
		# it would be CAMERA_MODEL, CAMERA_TYPE... 
		if value == None:
			for m in matrix['content']:
				if m['name'] == param and m['value'] == match:
					value = m['value']	
					
		if debug:
			print '\n------------ cond_check() ---------------'
			#print cdf_path
			#print prefix_etc_path
			print model 
			print 'param:%s' % param 
			print 'value:%s' % value 
			if flag:
				print 'match:%s' % match 
			else:
				print 'not match:%s' % match
			print '-----------------------------------------'


		if flag:
			if match == value:
				return True
			elif value != None and match in value:
				return True
			else:
				return False
		else:
			if match != value:
				return True
			else:
				return False


	def handle_detail_common_rule(self, matrix, content, index):

		rules = content['rule']
		name = content['param']

		for rule in rules:

			if debug:
				print '\n'

			m = self.check_cond(rule['cond'], matrix)
			if m:
				matrix['content'][index]['value'] = rule['value']
				if debug:
					print 'match!'
					print json.dumps(matrix, indent=4, sort_keys=True)
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

		# parse rule.json and save the info to matrix 
		for m in self.matrix:
			m['content'] = self.compose_dict_in_list(jdata['name'])
			for content in jdata['content']:
				# the index is for self.matrix[model]['content'][index]
				# and it would be used after the condition is matched
				index = jdata['content'].index(content)

				self.handle_detail_common_rule(m, content, index)


		print json.dumps(self.matrix, indent=4, sort_keys=True)
		print '\n\n'

	def parse_api_rule(self):
		data = open(self.api_rule).read()  
		jdata = json.loads(data)

		if not jdata.has_key('version') and not jdata.has_key('content'):
			error_msg()

		self.version = jdata['version']
		content = jdata['content']
		specs = jdata['content']['spec']

		# compose the self.matrix 
		# which contains all the information we need 

		for m in self.matrix:
			self.parse_detail_api_rule(m, specs)

		print json.dumps(self.matrix, indent=4, sort_keys=True)
		print '\n\n'

	def parse_detail_api_rule(self, matrix, specs):

		for spec in specs:
			questions = []
			tasks = []

			if spec.has_key('ques'):
				questions = spec['ques']

			if spec.has_key('task'):
				tasks = spec['task']

			for question in questions: 
				self.ask_user(question, matrix)

			for task in tasks: 
				if self.check_cond(task['cond'], matrix):
					#print task['cond']
					print 'match !!!!!!!!!!'
					matrix['action'] = matrix['action'] + task['action'] 
				else:
					#print task['cond']
					print 'not match ......'






class CommentedTreeBuilder ( et.XMLTreeBuilder ):
	def __init__ ( self, html = 0, target = None ):
		et.XMLTreeBuilder.__init__( self, html, target )
		self._parser.CommentHandler = self.handle_comment
    
	def handle_comment ( self, data ):
		self._target.start( et.Comment, {} )
		self._target.data( data )
		self._target.end( et.Comment )

# vim: tabstop=8 shiftwidth=8 softtabstop=8 noexpandtab
