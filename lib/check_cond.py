#!/usr/bin/env python

import sys, os
import re 
import json
from configer import *
from evaluator import *

debug = False 

def check_cond(cond, matrix):

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
			ret =  ret | check_detail_cond(s, matrix)
	elif len(sub_and) > 1:
		ret = True
		for s in sub_and:
			s = re.sub('\s+', '', s)
			ret =  ret & check_detail_cond(s, matrix)
	else:
		ret = check_detail_cond(cond, matrix)

	return ret


def check_detail_cond(cond, matrix):

	param = ''
	match = ''
	value = None 
	model = matrix['model']
	configer = matrix['configer']

	flag = True 

	cond = re.sub("'", "", cond)

	# eg. qid[1].val=1
	m = re.match('qid\[([^!]+)\].*=([^!]+)', cond)
	if m:
		answer = matrix['answer']
		qid = int(m.group(1))
		match = m.group(2)

		if answer.has_key(qid):
			value = answer[qid]
		else:
			return False


	# eg. qid[1].val!=1
	m = re.match('qid\[(.*)\].*!=(.*)', cond)
	if m:
		answer = matrix['answer']
		qid = int(m.group(1))
		match = m.group(2)

		flag = False 

		if answer.has_key(qid):
			value = answer[qid]
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


	# evaluate the param if needed
	tmp = Evaluator(param, [param], matrix)()	
	param = tmp[0]


	# use configer to fetch the parameter value
	if param != '' and value == None:
		value = configer.fetch_value(param)


	# if the value is None, it means that the parameter is not maintained by configer
	# it would be CAMERA_MODEL, CAMERA_TYPE ... 
	if value == None:
		if param in matrix['content'].keys():
			value = matrix['content'][param]
				
	if debug:
		print '\n----------- check condition -------------'
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
