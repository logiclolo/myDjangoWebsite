from ynm.models import Camera, Report
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
import json
import requests
from django.views.decorators.csrf import csrf_exempt

# Create your views here.
def camera(req):
	data = []

	if 'maintainer' in req.GET:
		cameras = Camera.objects.filter(maintainer__icontains = req.GET['maintainer']).order_by('maintainer')
		if len(reports) == 0:
			return response_error('Not found')
	elif 'modelname' in req.GET:
		cameras = Camera.objects.filter(modelname__icontains = req.GET['modelname']).order_by('maintainer')
		if len(reports) == 0:
			return response_error('Not found')
	else:
		cameras = Camera.objects.all().order_by('maintainer')

	for camera in cameras:
		tmp = fill_camera_data(camera)
		data.append(tmp)

	
	return response_ok(data)
	#return render(req, 'ynm/camera.html', {'cameras': cameras})

@csrf_exempt # for POST requests
def register(req):
	data = []

	if req.POST != None:
		print 'POST'
		add_camera(req.POST)
		cameras = Camera.objects.all()
		for camera in cameras:
			tmp = fill_camera_data(camera)
			data.append(tmp)
		
		return HttpResponseRedirect('/ynm/camera')
	elif req.GET != None:
		print 'GET'
		add_camera(req.GET)
		cameras = Camera.objects.all()
		for camera in cameras:
			tmp = fill_camera_data(camera)
			data.append(tmp)
		
		return HttpResponseRedirect('/ynm/camera')
		#return response_ok(data) 

@csrf_exempt # for POST requests
def update(req):
	data = []

	update_camera(req.POST)
	camera = Camera.objects.get(id = req.POST['id'])

	tmp = fill_camera_data(camera)
	data.append(tmp)

	return response_ok(data) 

def report(req):
	data = []

	if 'maintainer' in req.GET:
		reports = Report.objects.filter(camera__maintainer__icontains = req.GET['maintainer']).order_by('name')
		if len(reports) == 0:
			return response_error('Not found')
	elif 'modelname' in req.GET:
		reports = Report.objects.filter(camera__modelname__icontains = req.GET['modelname']).order_by('name')
		if len(reports) == 0:
			return response_error('Not found')
	elif 'show' in req.GET:
		report = Report.objects.get(id = req.GET['show'])
		tmp = report.content.read()
		return HttpResponse(tmp, content_type='text/plain')
	else:
		reports = Report.objects.all().order_by('name')

	for report in reports:
		tmp = fill_report_data(report)
		data.append(tmp)

	return response_ok(data) 

def response_ok(data):
	result = {}
	result['status'] = 'ok'
	result['data'] = data

	out = json.dumps(result, ensure_ascii = False)
	return HttpResponse(out, content_type = 'application/json')

def response_error(reason):
	result = {}
	result['status'] = 'error'
	result['reason'] = reason

	out = json.dumps(result, ensure_ascii = False)
	return HttpResponse(out, content_type = 'application/json')

def update_camera(obj):
	camera = Camera.objects.get(id = obj['id'])

	camera.maintainer = obj['maintainer'] 
	camera.modelname = obj['modelname'] 
	camera.macaddr = obj['macaddr'] 
	camera.ip = obj['ip']
	camera.platform = obj['platform']
	camera.account = obj['account']
	camera.passwd = obj['passwd']

	camera.save()

def add_camera(obj):
	camera = Camera()
	camera.maintainer = obj['maintainer'] 
	camera.modelname = obj['modelname'] 
	camera.macaddr = obj['macaddr'] 
	camera.ip = obj['ip']
	camera.platform = obj['platform']
	camera.account = obj['account']
	camera.passwd = obj['passwd']

	camera.save()

def fill_camera_data(obj):
	tmp = {}

	tmp['id'] = obj.id
	tmp['maintainer'] = obj.maintainer
	tmp['modelname'] = obj.modelname
	tmp['macaddr'] = obj.macaddr
	tmp['ip'] = obj.ip
	tmp['platform'] = obj.platform
	tmp['account'] = obj.account
	tmp['passwd'] = obj.passwd

	return tmp

def fill_report_data(obj):
	tmp = {}

	tmp['id'] = obj.id
	tmp['name'] = obj.name
	tmp['time'] = obj.time.strftime("%Y-%m-%d %H:%M:%S")
	tmp['maintainer'] = obj.camera.maintainer

	print tmp
	return tmp

def issue(obj):
	pass

def auto_test_request(obj):
	tmp = {}
	config = {}
	url = 'http://rd1-ci1.vivotek.tw/jenkins/job/onefw-ci-autotest/buildWithParameters/'
	token = 'run_onefw_auto_test'

	config['ip'] = obj.ip 
	config['mac'] = obj.macaddr 
	config['user'] = obj.account
	config['pass'] = obj.passwd 

	tmp['config'] = str(config)
	tmp['token'] = token 

	r = requests.post(url, data=tmp)
	#print r.status_code


# vim: tabstop=8 shiftwidth=8 softtabstop=8 noexpandtab
