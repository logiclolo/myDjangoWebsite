import sys, os
import re 
import json
from pprint import pprint
from xml.dom import minidom
from lxml import etree
import subprocess
import HTMLParser
import bcolors
from copy import deepcopy
from configer import *
from check_cond import *
from evaluator import *
from xml_updater import *
from utility import *
import config

if sys.version_info[:2] >= (2, 5):
	import xml.etree.ElementTree as et 
else:
	import elementtree.ElementTree as et 

class Dispatcher(object):

	def __init__(self, action, matrix):
		self.confile = action['file'] 
		self.contents = action['content']
		self.matrix = matrix

		self.get_file_path()
		
		path = self.matrix['path']
		if path != '':
			self.et_object = et.parse(path, CommentedTreeBuilder())
			self.et_root = self.et_object.getroot()

			self.read_xml_declaration(path)
		else:
			return None 

		#  'modify xml tree' or 'just format'
		if config.g_format:
			if not path in config.g_format_list: 
				config.g_format_list.append(path)
				print 'formatting ... %s' % path
				XmlWriter(self.et_root, self.matrix)
		else:
			print 'Modifying ... %s' % path
			self.dispatch()

	def read_xml_declaration(self, path):
		
		fh = open(path, 'r')
		tmp = fh.readline()

		tmp = re.sub('\n', '', tmp)
		m = re.search('<\?.*\?>', tmp)
		if m:
			self.matrix['declaration'] = tmp
		else:
			self.matrix['declaration'] = None 

	def get_file_path(self):

		self.matrix['path'] = '' 
		model = self.matrix['model']
		confile = self.confile

		self.matrix['path'] = locate_file(model, confile)

	def apply_xml_updater(self, md, content):
		matrix = self.matrix
		et_object = self.et_object

		obj = md(et_object, content['element'], matrix)
		return obj.action()

	def dispatch(self):
		ret = False 
		contents = self.contents

		for content in contents:
			md = content['method']
			if md == 'add':
				ret = self.apply_xml_updater(Add, content)
			elif md == 'modify':
				ret = self.apply_xml_updater(Modify, content)
			elif md == 'remove':
				ret = self.apply_xml_updater(Remove, content)

		if ret:
			XmlWriter(self.et_root, self.matrix)


class XmlWriter(object):

	def __init__(self, elem, matrix):
		path = matrix['path']
		self.xml_declaration = matrix['declaration']
		content = self.prettify(elem, path)
		self.output(path, content)


	def prettify(self, elem, path):
		# Return a pretty-printed XML string for the Element.
		rough_string = et.tostring(elem, encoding='utf-8')
		reparsed = minidom.parseString(rough_string)
		tmp = reparsed.toprettyxml(indent="\t")
		
		# remove the redundant line
		tmp = re.sub('(\t+\s*\n+)+', '', tmp) 


		# handle xml declaration
		if self.xml_declaration is not None:
			tmp = re.sub('<\?.*\?>', self.xml_declaration, tmp)
		else:
			tmp = re.sub('<\?.*\?>\n', '', tmp)


		# handle different situation under CDF and config
		# It's a workaround ... need more good solution
		if os.path.basename(path) == 'CDF.xml':
			tmp = re.sub('<root>', '<root xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">', tmp)
		else:
			# replace <tag/> with <tag></tag>
			tmp = re.sub(r'<(.*)/>', r'<\1></\1>', tmp)


		# handle the escape
		# eg. &quot, &lt, &gt
		h = HTMLParser.HTMLParser()
		xml_content = h.unescape(tmp)

		return xml_content 

	def output(self, filename, content):
		try:
			outh = open(filename,'w')
		except IOError, e:
			print e

		outh.write(content)

# vim: tabstop=8 shiftwidth=8 softtabstop=8 noexpandtab
