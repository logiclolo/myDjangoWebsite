#!/usr/bin/env python
#encoding: utf-8

import sys, os
import re 
import json
import bcolors
import subprocess
import pprint
import config 
from copy import deepcopy
from configer import *


def output(filename, content):
	try:
		outh = open(filename,'w')
	except IOError, e:
		print e

	outh.write(content)

def available_model():
	tmp = []
	capability = 'config_capability.xml'

	flashfs_base = os.path.join(os.getenv('PRODUCTDIR'), 'flashfs_base')  
	dirs = subprocess.Popen('find %s -iname %s' % (flashfs_base, capability), shell=True, stdout = subprocess.PIPE).stdout
	for d in dirs: 	
		d = re.sub('\n', '', d)
		m = re.search('.*/([A-Z][A-Z][0-9A-Z]+)/.*', d)
		if m:
			tmp.append(m.group(1))

	return tmp

def choose_model(model_file):
	if os.path.isfile(model_file):
		tmp = []
		try:
			fh = open(model_file, 'r')
			line = fh.readline()

			while line:
				line = re.sub('[\r\n$()]', '', line)
				tmp.append(line)

				line = fh.readline()

			model = strip_model(tmp)

			if config.g_format:
				option = 'format'
			else:
				option = 'update'

			print bcolors.WARNING + 'We are going to %s the CDF/configs of:' % option
			print model
			print bcolors.NORMAL


		except IOError, e:
			print e
			sys.exit(1)
	else:
		model = available_model()

		tmp = ''
		for m in model:
			tmp = tmp + m + '\n'

		output(model_file, tmp)

		if config.g_format:
			option = 'format'
		else:
			option = 'update'

		print 'Configurator will %s the CDF/configs of model according to \'%s\'' % (option, model_file)
		print bcolors.WARNING + 'We generate the \'%s\' for you and ready to %s CDF/configs of:' % (model_file, option)
		print model
		print bcolors.NORMAL


	if len(model) == 0:
		print 'No models. Please modify \'%s\'' % model_file	
		sys.exit(0)

	print 'Modify \'%s\' if you want to change models' % model_file
	print 'Press any key to continue or \'q\' to exit ...'

	ans = getch()
	if ans == 'q':
		sys.exit(0)

	return model

def find_current_api(matrix):

	configer = matrix['configer']
	value = configer.fetch_value('capability_api_httpversion')

	if value != None:
		value = value.split('_')[0]
		value = value + '.json'

	return value 
	

def choose_api(api, matrix):

	basename = os.path.basename(api)
	dirname = os.path.dirname(api)

	totals = os.listdir(dirname)
	totals.sort()

	current = find_current_api(matrix)

	try:
		index1 = totals.index(current)
		index2 = totals.index(basename)
		totals = totals[(index1 + 1):(index2 + 1)]

	except ValueError:
		# current api is not found in database
		# update latest api only
		index2 = totals.index(basename)
		totals = totals[index2:(index2 + 1)]

	print bcolors.GOOD + '\n%s' % matrix['model'] + bcolors.NORMAL
	print 'current api   :' + str([current.split('.')[0]])
	tmp = []
	if len(totals) != 0:
		for api in totals:
			tmp.append(api.split('.')[0])
		print 'api to upgrade:' + str(tmp)
	else:
		print 'api to upgrade: None' 

	# return api with path
	tmp = []
	for t in totals:
		tmp.append(os.path.join(dirname, t))

	return tmp 

def show_all_api():

	totals = os.listdir('api')
	totals.sort()

	# no need to show rule.json
	totals = totals[:-1]

	print totals


def strip_model(model):
	tmp = []

	flashfs_base = os.path.join(os.getenv('PRODUCTDIR'), 'flashfs_base')  
	for m in model:
		path = os.path.join(flashfs_base, m)
		if os.path.isdir(path):
			tmp.append(m)
		else:
			print bcolors.WARNING + m + bcolors.NORMAL + ' does not exist. We won\'t update it.' 

	return tmp


def locate_file(model, confile):

	# search in 'flashfs_base' first
	flashfs_base = os.path.join(os.getenv('PRODUCTDIR'), 'flashfs_base')  
	base = os.path.join(flashfs_base, model)  
	cmd = 'find %s -iname %s' % (base, confile)
	path = subprocess.Popen(cmd, shell=True, stdout = subprocess.PIPE).stdout
	for p in path: 	
		p = re.sub('\n', '', p)
		return p

	# and then search in 'common'
	base = os.path.join(flashfs_base, 'common')
	cmd = 'find %s -iname %s' % (base, confile)
	path = subprocess.Popen(cmd, shell=True, stdout = subprocess.PIPE).stdout
	for p in path: 	
		p = re.sub('\n', '', p)
		return p

	return None 

def record_xml_update_err(path, xpath, method):
	config.g_update_err_list.append((path, xpath, method))

def xml_update_err_show():

	for u in config.g_update_list:
		tmp_modify = []
		tmp_remove = []
		tmp_add = []

		print 'Upgrading ... %s' % u

		for err in config.g_update_err_list:
			if u == err[0]:
				xpaths = err[1].split('&')
				for xpath in xpaths:
					method = err[2]
					if method == 'add':
						tmp_add.append(xpath)
					elif method == 'remove': 
						tmp_remove.append(xpath)
					elif method == 'modify': 
						tmp_modify.append(xpath)

		if len(tmp_modify) > 0:
			print '\n\t(修改...)'
			for tmp in tmp_modify:
				print bcolors.BLUE + '\t\'%s\'' % tmp 
			print '\t' + bcolors.NORMAL + '以上參數不存在'

		if len(tmp_remove) > 0:
			print '\n\t(刪除...)'
			for tmp in tmp_remove:
				print bcolors.BLUE + '\t\'%s\'' % tmp 
			print '\t' + bcolors.NORMAL + u'以上參數本來就不存在'

		if len(tmp_add) > 0:
			print '\n\t(新增...)'
			for tmp in tmp_add:
				print bcolors.BLUE + '\t\'%s\'' % tmp 
			print '\t' + bcolors.NORMAL + '以上參數已經存在'


		print bcolors.NORMAL




def is_xml_well_formed(path):
	tmp = []
	cflag = 'end' # flag for comment line

	fh = open(path, 'r')
	line = fh.readline()
	line_count = 1 

	while line:
		# <root>...</root>
		m1 = re.match('\t*\s*<[^/]+>[^<>]*</.+>$', line)
		# <root>
		m2 = re.match('\t*\s*<[^/]+>$', line)
		# </root>
		m3 = re.match('\t*\s*</.+>$', line)

		# <!-- ... -->
		m4 = re.match('\t*\s*<!--.*-->', line)
		# <!-- 
		m5 = re.match('\t*\s*<!--', line)
		# --> 
		m6 = re.match('\t*\s*-->', line)

		# <root/>
		m7 = re.match('\t*\s*<.+/>$', line)

		# /t<root>
		m8 = re.match('\t+<[^/]+>$', line)


		if m5:
			cflag = 'start'
		elif m6:
			cflag = 'end'
		elif m7:
			if os.path.basename(path) == 'CDF.xml':
				pass
			else:
				tmp.append(repr(line))
		elif line_count == 1 and m8:
			tmp.append(repr(line))
		elif m1 or m2 or m3 or m4:
			pass
		else:
			if cflag == 'end':
				tmp.append(repr(line))

		line = fh.readline()
		line_count = line_count + 1

	if len(tmp) > 0:
		#pp = pprint.PrettyPrinter(indent=4)
		#pp.pprint(tmp)
		return False 
	else:
		return True


def jason_default(o):
	if isinstance(o, set):
		return list(o)
	return o.__dict__


class _Getch:
    """Gets a single character from standard input.  Does not echo to the screen."""
    def __init__(self):
        try:
            self.impl = _GetchWindows()
        except ImportError:
            self.impl = _GetchUnix()

    def __call__(self): return self.impl()


class _GetchUnix:
    def __init__(self):
        import tty, sys

    def __call__(self):
        import sys, tty, termios
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch


class _GetchWindows:
    def __init__(self):
        import msvcrt

    def __call__(self):
        import msvcrt
        return msvcrt.getch()


getch = _Getch()

# vim: tabstop=8 shiftwidth=8 softtabstop=8 noexpandtab
