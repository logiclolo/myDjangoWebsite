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
from copy import deepcopy
from configer import *
from check_cond import *
from evaluator import *

if sys.version_info[:2] >= (2, 5):
	import xml.etree.ElementTree as et 
else:
	import elementtree.ElementTree as et 

#debug = True 
debug = False 

class Base(object):
	confile = ''
	method = ''
	matrix = {}
	matrix_action = {} 
	matrix_contents = []
	matrix_model = ''

	def __init__(self, et_object, elements, matrix):
		self.matrix = matrix
		self.elements = elements
		self.et_object = et_object
		self.param_exist_already = True

		self.compose_detail_action()

		if debug:
			print json.dumps(self.elements, indent=4, sort_keys=True)

	def compose_detail_action(self):

		elements = self.elements

		for element in elements:
			xpaths = element['param']
			element['xpath'] = [] 

			for xpath in xpaths.split('&'):
				element['xpath'].append(deepcopy(xpath))

				m = re.search('<.*>', xpath)
				if m:
					# The evaluated result is saved to element['xpath']  
					# and after that self.action() would use these detail
					element['xpath'] = Evaluator(xpath, element['xpath'], self.matrix)()

	def action(self):

		stain = False 

		elements = self.elements
		et_object = self.et_object

		for element in elements:
			if element.has_key('cond') and not check_cond(element['cond'], self.matrix): 
				continue

			stain = stain | self.detail_action(et_object, element)

		if stain:
			return True 
		else:
			return False 


class Add(Base):
	""" Add the tag into XML """

	def detail_action(self, et_object, element):
		et_new_node =  self.insert_new_xpath(et_object, element)

		if et_new_node != None or self.param_exist_already:
			return True
		else:
			print '\t' + bcolors.WARNING + '\'%s\'' % element['param'] + bcolors.NORMAL + ' exists already !'
			return False

	def insert_new_xpath(self, et_object, element):

		et_new_node = None
		et_ori_object = et_object
		xpaths = element['xpath']

		for xpath in xpaths:
			# travel every node of the given xpath
			# if the node is not in the xml tree, then insert it
			trace = xpath.split('_')
			for node in trace:
				ori_object = et_object
				et_object = et_object.find(node)
				if et_object == None:
					self.param_exist_already = False
					et_new_node = et.Element(node)

					# the last node in the xpath
					if  node == trace[-1]:
						self.handle_last_node(element, et_new_node, ori_object)


					ori_object.append(et_new_node)
					et_object = ori_object.find(node)

			if self.param_exist_already:
				self.handle_last_node(element, et_object, ori_object)
			et_object = et_ori_object

		return et_new_node

	def handle_last_node(self, element, et_new_node, ori_object):

		et_new_value_node = None 

		# Handle ordinary config
		if element.has_key('value'):
			value = str(element['value'])
			m = re.match('\?(.*)', value)
			if m:
				# default value
				et_new_node.text = m.group(1)
				#et_comment_node = et.Comment('[Notice] Please modify the default value below !!!')
				et_comment_node = et.Comment('Modify it')
				ori_object.append(et_comment_node)
			else:
				et_new_node.text = value

		# Handle CDF ...
		if element.has_key('check'):
			check = element['check']
			if self.param_exist_already != True:
				# <check>
				if check != None and check != 'null':
					check = str(check)
					et_new_check_node = et.Element('check')

				m = re.match('\?(.*)', check)
				if m:
					# default check value
					et_new_check_node.text = m.group(1)
					#et_comment_node = et.Comment('[Notice] Please modify the check value below !!!')
					et_comment_node = et.Comment('Modify it')
					et_new_node.append(et_comment_node)
				else:
					et_new_check_node.text = check
					et_new_node.append(et_new_check_node)

			# <value>
			if not et_new_value_node:
				et_new_value_node = et.Element('value')
				et_new_node.append(et_new_value_node)


		# Handle CDF ...  
		if element.has_key('aliasxpath'):
			aliasxpath = element['aliasxpath']

			tmp = Evaluator(aliasxpath, [aliasxpath], self.matrix)()	
			aliasxpath = tmp[0]

			# <aliasxpath>
			et_new_aliasxpath_node = et.Element('aliasxpath')
			et_new_aliasxpath_node.text = aliasxpath
			et_new_node.append(et_new_aliasxpath_node)

			# <value>
			if not et_new_value_node:
				et_new_value_node = et.Element('value')
				et_new_node.append(et_new_value_node)

class Remove(Base):
	""" Remove the tag from XML """

	def detail_action(self, et_object, element):
		ret =  self.remove_xpath(et_object, element)

		if ret:
			return True
		else:
			print '\t' + bcolors.WARNING + '\'%s\'' % element['param'] + bcolors.NORMAL + ' does not exist !' 
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



class Modify(Base):
	""" Modify the XML tag content """

	def detail_action(self, et_object, element):
		stain = False

		xpaths = element['xpath']

		for xpath in xpaths:
			xpath = re.sub('_', '/', xpath)
			et_target_tag = et_object.find(xpath)

			if et_target_tag is not None:
				self.handle_last_node(et_target_tag, element)
				stain = True

		if not stain:
			print '\t' + bcolors.WARNING + '\'%s\'' % element['param'] + bcolors.NORMAL + ' does not exist !' 

		return stain

	def handle_last_node(self, et_target_tag, element):
		# Handle ordinary config
		if element.has_key('value'):
			value = str(element['value'])
			m = re.match('\?(.*)', value)
			if m:
				# default value
				et_target_tag.text = m.group(1) 
			else:
				et_target_tag.text = value 

		# Handle CDF
		if element.has_key('check'):
			et_child_tag = et_target_tag.find('check')

			if et_child_tag != None: 
				value = str(element['check'])

				# if value start with '+' or '-'
				m1 = re.match('\+(.*)', value)
				m2 = re.match('\-(.*)', value)
				if m1:
					self.insert_sub_text(et_child_tag, m1.group(1))
				elif m2:
					self.remove_sub_text(et_child_tag, m2.group(1))
				else:	
					et_child_tag.text = value 

	def insert_sub_text(self, et_child_tag, sub_text):
		subs = []
		text = et_child_tag.text
		m = re.search('(".*").*"(.*)"', text)
		if m:
			subs = m.group(2).split(',')
			subs.append(sub_text)
			value = m.group(1) + ',"' + ','.join(subs) + '"'
			et_child_tag.text = value


	def remove_sub_text(self, et_child_tag, sub_text):
		subs = []
		text = et_child_tag.text
		m = re.search('(".*").*"(.*)"', text)
		if m:
			subs = m.group(2).split(',')
			if sub_text in subs:
				subs.remove(sub_text)
			value = m.group(1) + ',"' + ','.join(subs) + '"'
			et_child_tag.text = value


class CommentedTreeBuilder ( et.XMLTreeBuilder ):
	def __init__ ( self, html = 0, target = None ):
		et.XMLTreeBuilder.__init__( self, html, target )
		self._parser.CommentHandler = self.handle_comment
    
	def handle_comment ( self, data ):
		self._target.start( et.Comment, {} )
		self._target.data( data )
		self._target.end( et.Comment )


# vim: tabstop=8 shiftwidth=8 softtabstop=8 noexpandtab
