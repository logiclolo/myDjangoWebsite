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

if sys.version_info[:2] >= (2, 5):
	import xml.etree.ElementTree as et 
else:
	import elementtree.ElementTree as et 

class Dispatcher(object):

	def __init__(self, action, matrix):
		self.confile = action['file'] 
		self.contents = action['content']
		self.matrix = matrix

		self.locate_config()
		
		path = self.matrix['path']
		if path != '':
			print '\n%s' % path
			self.et_object = et.parse(path, CommentedTreeBuilder())
			self.et_root = self.et_object.getroot()
		else:
			return None 

		self.dispatch()

	def locate_config(self):

		self.matrix['path'] = '' 
		model = self.matrix['model']
		confile = self.confile

		directory = os.path.join(os.getenv('PRODUCTDIR'), 'flashfs_base', model)  
		path = subprocess.Popen('find %s -iname %s' % (directory, confile), shell=True, stdout = subprocess.PIPE).stdout
		for p in path: 	
			p = re.sub('\n', '', p)
			self.matrix['path'] = p

		# the file could be in 'common'
		if len(self.matrix['path']) == 0:
			flash_base = os.path.join(os.getenv('PRODUCTDIR'), 'flashfs_base', 'common')
			path = subprocess.Popen('find %s -iname %s' % (flash_base, confile), shell=True, stdout = subprocess.PIPE).stdout
			for p in path: 	
				p = re.sub('\n', '', p)
				self.matrix['path'] = p


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
			XmlWriter(self.et_root, self.matrix['path'])


class XmlWriter(object):

	def __init__(self, elem, path):
		content = self.prettify(elem, path)
		self.output(path, content)


	def prettify(self, elem, path):
		# Return a pretty-printed XML string for the Element.
		rough_string = et.tostring(elem, encoding='utf-8')
		reparsed = minidom.parseString(rough_string)
		tmp = reparsed.toprettyxml(indent="\t")
		
		# remove the redundant line
		tmp = re.sub('(\t+\s*\n+)+', '', tmp) 


		# handle different situation under CDF and config
		# It's a workaround ... need more good solution
		if re.search('CDF', path):
			tmp = re.sub('<\?.*\?>', '<?xml version="1.0" encoding="UTF-8"?>', tmp)
			tmp = re.sub('<root>', '<root xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">', tmp)
		else:
			# replace <tag/> with <tag></tag>
			tmp = re.sub('<\?.*\?>\n', '', tmp)
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
