import sys, os
import re 
import json
from copy import deepcopy
from configer import *

class Evaluator(object):
	# Evaluate c<n>, s<m> or <TOTALSTREAMNUM> in the parameter 
	#
	# the __call__ returns a list
	

	def __init__(self, param, xpath, matrix):
		self.param = param
		self.xpath = xpath
		self.matrix = matrix

	def eval_channel_number(self):
		tmp = []
		for x in self.xpath:
			value = re.sub('<n>', '0', x)
			tmp.append(value)
		self.xpath = deepcopy(tmp)

	def eval_stream_number(self):
		xpath = self.xpath
		model = self.matrix['model']

		stream_number = Configer(model).fetch_value('capability_nmediastream')
		stream_number = int(stream_number)

		tmp = []
		for x in xpath:
			for i in range(0, stream_number):
				value = re.sub('<m>', '%d' % i, x)
				tmp.append(value)
		self.xpath = deepcopy(tmp)

	def eval_qid_answer(self, match):
		xpath = self.xpath

		index = int(match)
		number = self.matrix['answer'][index]
		number = int(number)

		tmp = []
		for x in xpath:
			for i in range(0, number):
				value = re.sub('<qid\[%d\].val>' % index, '%d' % i, x)
				tmp.append(value)
		self.xpath = deepcopy(tmp)

	def eval_internal_param(self, match):
		xpath = self.xpath
		content = self.matrix['content']

		if match in content.keys():
			number = content[match]	
			number = int(number)
			tmp = []
			for x in xpath:
				for i in range(0, number): 
					value = re.sub('<[A-Z]+>', '%d' % i, x)
					tmp.append(value)
			self.xpath = deepcopy(tmp)


	def __call__(self):
		param = self.param
		m = re.search('<n>', param)
		if m:
			self.eval_channel_number()	

		m = re.search('<m>', param)
		if m:
			self.eval_stream_number()

		m = re.search('<qid\[(\d+)\]\.val>', param)
		if m:
			self.eval_qid_answer(m.group(1))

		m = re.search('<([A-Z]+)>', param)
		if m:
			self.eval_internal_param(m.group(1))

		return self.xpath

# vim: tabstop=8 shiftwidth=8 softtabstop=8 noexpandtab
