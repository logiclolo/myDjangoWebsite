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
from info_collector import *

if sys.version_info[:2] >= (2, 5):
	import xml.etree.ElementTree as et
else:
	import elementtree.ElementTree as et

class RuleParser(object):
	version = ''
	api_rule = ''
	common_rule = ''
	actions = []
	config_path = []
	matrix = []

	def __init__(self, path, models):
		self.api_rule = path
		self.common_rule = './api/rule.json'
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

		tmp = {}
		for model in self.models:
			tmp['model'] = model
			tmp['action'] = []
			tmp['content'] = []
			tmp['answer'] = {}
			self.matrix.append(deepcopy(tmp))

	def handle_detail_common_rule(self, matrix, content):

		rules = content['rule']
		name = content['param']

		for rule in rules:
			if check_cond(rule['cond'], matrix):
				matrix['content'][name] = rule['value']
				break

	def compose_internal_param_dict(self, name, matrix):
		for key, value in name.iteritems():
			m = re.search('_', str(value))
			if m:
				value = Configer(matrix['model']).fetch_value(str(value))
				name[key] = value
		return deepcopy(name)

	def check_file_well_formed(self):
		data = open(self.api_rule).read()
		jdata = json.loads(data)

		if not jdata.has_key('version') and not jdata.has_key('content'):
			error_msg()

		self.version = jdata['version']
		content = jdata['content']
		specs = jdata['content']['spec']

		confiles = []
		for spec in specs:
			tasks = spec['task']
			for task in tasks:
				actions = task['action']
				for action in actions:
					config = action['file']
					confiles.append(config)

		confile_path = []
		for model in self.models:
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
			m['content'] = self.compose_internal_param_dict(jdata['name'], m)
			for content in jdata['content']:
				self.handle_detail_common_rule(m, content)


		if debug:
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

		if debug:
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
					matrix['action'] = matrix['action'] + task['action']






# vim: tabstop=8 shiftwidth=8 softtabstop=8 noexpandtab
