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
from check_cond import *

if sys.version_info[:2] >= (2, 5):
	import xml.etree.ElementTree as et 
else:
	import elementtree.ElementTree as et 

debug = True

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
		if check_cond(question['cond'], matrix):
			ques = question['ask']

			print '\nPlease answer the questions based on \'%s\' ...' % matrix['model'] 
			print ques 
			ans = raw_input()
			while not self.check_answer(ques, ans):
				ans = raw_input()
			
			#question['ans'] = ans
			qid = question['id']
			print matrix['answer']
			matrix['answer'][qid] = ans
		else:
			print 'No need to ask.'

	def initial_matrix(self):

		# The matrix contains the main infomation we need
		# and the length of matrix is 'numbers of model'
		#
		# What initial_matrix() does: 
		#
		# (1) Find numbers of model 
		# Use config_capability.xml to find models 
		#
		# (2) action list
		# It saves the result after parsing the 'api_version.json' 
		# Just initial here 
		# 
		# (3) content list
		# It saves the result after parsing rule.json
		#
		# (4) answer list
		# The replies answerd by the user  

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
			tmp['answer'] = ['']*20 # initial the list with null 
			self.matrix.append(deepcopy(tmp))

	def check_cond(self, cond, matrix):

		ret = False

		if cond == True or cond == 'true':
			if debug:
				print '\n------------ check condition ---------------'
				print 'cond: %s' % cond
				print '-----------------------------------------'

			return True


		sub_or = cond.split('||')
		sub_and = cond.split('&&')
		if len(sub_or) > 1:
			for s in sub_or:
				s = re.sub('\s+', '', s)
				ret =  ret | self.check_detail_cond(s, matrix)
		elif len(sub_and) > 1:
			ret = True
			for s in sub_and:
				s = re.sub('\s+', '', s)
				ret =  ret & self.check_detail_cond(s, matrix)
		else:
			ret = self.check_detail_cond(cond, matrix)

		return ret


	def check_detail_cond(self, cond, matrix):

		param = ''
		match = ''
		model = matrix['model']

		flag = True 
		value = None

		cond = re.sub("'", "", cond)

		# eg. qid[1].val=1
		m = re.match('qid\[(.*)\].*=(.*)', cond)
		if m:
			answer = matrix['answer']
			qid = int(m.group(1))
			match = m.group(2)

			if qid > len(answer): 
				return False
			elif answer[qid] == match:
				return True
			else:
				return False
				

		# eg. 'FD' in 'system_info_extendedmodelname'
		m = re.match('(.*)\sin\s(.*)', cond)
		if m:
			match = m.group(1)
			param = m.group(2)	
			

		# eg. capability_fisheye=1
		m = re.match('([^!]+)=([^!]+)', cond)
		if m:
			param = m.group(1)	
			match = m.group(2)

		# eg. CAMERA_TYPE!=VC
		m = re.match('(.*)!=(.*)', cond)
		if m:
			flag = False 
			param = m.group(1)	
			match = m.group(2)

		# use configer to fetch the parameter value
		if param != '':
			flash_base = os.path.join(os.getenv('PRODUCTDIR'), 'flashfs_base')  
			cdf_path = os.path.join(flash_base, model, 'etc', 'CDF.xml')
			prefix_etc_path = os.path.join(flash_base, model)

			value = fetch_value_from_configer(cdf_path, prefix_etc_path, param)



		# if the value is None, it means that the parameter is not maintained by configer
		# it would be CAMERA_MODEL, CAMERA_TYPE ... 
		if value == None:
			for m in matrix['content']:
				if m['name'] == param:
					value = m['value']	
					
		if debug:
			print '\n------------ check condition ---------------'
			#print cdf_path
			#print prefix_etc_path
			print 'model:%s' % model 
			print 'param:%s' % param 
			print 'value:%s' % value 
			if flag:
				print 'match:%s' % match 
			else:
				print 'not match:%s' % match
			print '-----------------------------------------'


		match = str(match).lower()
		value = str(value).lower()

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

			m = check_cond(rule['cond'], matrix)
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
			for key, value in name.iteritems():
				dictp['name'] = key
				dictp['value'] = value 
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
				if check_cond(task['cond'], matrix):
					#print task['cond']
					print 'match !!!!!!!!!!'
					matrix['action'] = matrix['action'] + task['action'] 
				else:
					#print task['cond']
					print 'not match ......'






# vim: tabstop=8 shiftwidth=8 softtabstop=8 noexpandtab
