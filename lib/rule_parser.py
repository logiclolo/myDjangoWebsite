#!/usr/bin/env python

import sys, os
import re
import json
from pprint import pprint
from xml.dom import minidom
from lxml import etree
import subprocess
import HTMLParser
import bcolors
import pprint
from utility import *
from copy import deepcopy
from configer import *
from check_cond import *
import config

if sys.version_info[:2] >= (2, 5):
	import xml.etree.ElementTree as et
else:
	import elementtree.ElementTree as et

class RuleParser(object):
	latest_api = ''
	common_rule = ''
	actions = []
	config_path = []
	matrix = []
	update_api_list = []

	def __init__(self, path, models):
		self.latest_api = path
		dirname = os.path.dirname(path)
		self.common_rule = os.path.join(dirname, 'rule.json')
		self.models = models

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
			print bcolors.WARNING + ques + bcolors.NORMAL
			if question.has_key('range'):
				print '(range is %s)' % question['range']
			ans = raw_input()
			while not self.check_answer(ques, ans):
				ans = raw_input()

			#question['ans'] = ans
			qid = question['id']
			matrix['answer'][qid] = ans
		#else:
			#print 'No need to ask.'

	def initial_matrix(self):

		# The matrix contains the main infomation we need
		# and the length of matrix is 'numbers of model'
		#
		# What initial_matrix() does:
		#
		# (1) get model name
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
		# 
		# (5) update list
		# The list of all the api for upgrade 

		tmp = {}
		for model in self.models:
			tmp['model'] = model
			tmp['action'] = []
			tmp['content'] = []
			tmp['update'] = []
			tmp['answer'] = {}
			self.matrix.append(deepcopy(tmp))

	def clean_matrix(self):
		for matrix in self.matrix:
			matrix['action'] = []
			matrix['answer'] = {} 

		config.g_format_list = []
		config.g_update_list = []
		config.g_update_err_list = []

	def handle_detail_common_rule(self, matrix, content):

		rules = content['rule']
		name = content['param']

		for rule in rules:
			if check_cond(rule['cond'], matrix):
				matrix['content'][name] = rule['value']
				break

	def compose_internal_param_dict(self, name, matrix):
		tmp = deepcopy(name)
		for key, value in tmp.iteritems():
			m = re.search('_', str(value))
			if m:
				value = matrix['configer'].fetch_value(str(value))
				tmp[key] = value
		return deepcopy(tmp)

	def check_file_well_formed(self, api_path, model):
		data = open(api_path).read()
		jdata = json.loads(data)

		if not jdata.has_key('version') and not jdata.has_key('content'):
			error_msg()

		version = jdata['version']
		specs = jdata['content']['spec']

		confiles = []
		for spec in specs:
			tasks = spec['task']
			for task in tasks:
				actions = task['action']
				for action in actions:
					if action.has_key('file'):
						config = action['file']
						confiles.append(config)

		confile_path = []
		for confile in confiles:
			tmp = locate_file(model, confile)
			if tmp not in confile_path:
				confile_path.append(tmp)

		ret = []
		for path in confile_path:
			if not is_xml_well_formed(path):
				ret.append(path)

		return ret

	def parse_common_rule(self):
		data = open(self.common_rule).read()
		jdata = json.loads(data)

		if not jdata.has_key('name') and not jdata.has_key('content'):
			error_msg()

		# parse rule.json and save the info to matrix
		for m in self.matrix:
			configer = Configer(m['model'])
			m['configer'] = configer

			m['content'] = self.compose_internal_param_dict(jdata['name'], m)
			for content in jdata['content']:
				self.handle_detail_common_rule(m, content)

			configer.stop()

			# all the APIs need to update
			m['update'] = choose_api(self.latest_api, m['model'])


		if debug:
			print json.dumps(self.matrix, indent=4, sort_keys=True, default=jason_default)
			print '\n\n'

	def parse_api_rule(self, api_path, model):
		data = open(api_path).read()
		jdata = json.loads(data)

		if not jdata.has_key('version') and not jdata.has_key('content'):
			error_msg()

		version = jdata['version']
		specs = jdata['content']['spec']

		print bcolors.WARNING + '----------------------------'
		print '%s' % version
		print '----------------------------' + bcolors.NORMAL

		self.clean_matrix()

		# find the matrix with specific model
		for matrix in self.matrix:
			if model == matrix['model']:
				break

		configer = Configer(model)
		matrix['configer'] = configer

		# compose the model matrix 
		# which contains all the information we need
		self.parse_detail_api_rule(matrix, specs)

		configer.stop()

		if debug:
			print json.dumps(matrix, indent=4, sort_keys=True, default=jason_default)
			print '\n\n'

	def parse_detail_api_rule(self, matrix, specs):

		for spec in specs:
			questions = []
			tasks = []

			if spec.has_key('ques'):
				questions = spec['ques']

			if spec.has_key('task'):
				tasks = spec['task']

			# format or update 
			if config.g_format:
				for task in tasks:
					matrix['action'] = matrix['action'] + task['action']
			else:
				for question in questions:
					self.ask_user(question, matrix)

				for task in tasks:
					if check_cond(task['cond'], matrix):
						matrix['action'] = matrix['action'] + task['action']






# vim: tabstop=8 shiftwidth=8 softtabstop=8 noexpandtab
