import sys, os
import re 
import json
from copy import deepcopy
from configer import *

class Evaluator(object):
	# find c<n>, s<m> or <..> 
	# and replace the variable with real number/value

	def __init__(self, param, xpath, model):
		self.param = param
		self.xpath = xpath
		self.model = model

	def eval_channel_number(self):
		tmp = []
		for x in self.xpath:
			value = re.sub('<n>', '0', x)
			tmp.append(value)
		self.xpath = deepcopy(tmp)

	def eval_stream_number(self):
		stream_number = Configer(self.model).fetch_value('capability_nmediastream')
		xpath = self.xpath

		tmp = []
		for x in xpath:
			for i in range(0, int(stream_number)):
				value = re.sub('<m>', '%d' % i, x)
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

		return self.xpath

# vim: tabstop=8 shiftwidth=8 softtabstop=8 noexpandtab
