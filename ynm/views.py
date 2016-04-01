from ynm.models import Camera, Report
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
import json
import requests
from django.views.decorators.csrf import csrf_exempt

platform = {
	'Rossini'             : 1,
	'Hisillicon Standard' : 2,
	'Hisillicon Speeddome': 3,
}

url = 'http://rd1-ci1.vivotek.tw/jenkins/job/onefw-ci-autotest/buildWithParameters/'
token = 'run_onefw_auto_test'


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

	if req.method != 'POST':
		return response_error('Invalid method');

	jdata = json.loads(req.body)
	update_camera(jdata, 'add')

	# fetch the latest one
	camera = Camera.objects.all().order_by('-id')[0]
	tmp = fill_camera_data(camera)
	data.append(tmp)
	
	return response_ok(data) 

@csrf_exempt # for POST requests
def update(req):
	data = []

	if req.method != 'POST':
		return response_error('Invalid method');

	jdata = json.loads(req.body)
	update_camera(jdata, 'update')

	camera = Camera.objects.get(id = jdata['id'])
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

def update_camera(obj, method):
	if method == 'add':
		camera = Camera()
	elif method == 'update':
		camera = Camera.objects.get(id = obj['id'])
	else:
		return None

	if obj.has_key('maintainer'):
		camera.maintainer = obj['maintainer'] 
	if obj.has_key('modelname'):
		camera.modelname = obj['modelname'] 
	if obj.has_key('macaddr'):
		camera.macaddr = obj['macaddr'] 
	if obj.has_key('ip'):
		camera.ip = obj['ip']
	if obj.has_key('platform'):
		camera.platform = obj['platform']
	if obj.has_key('account'):
		camera.account = obj['account']
	if obj.has_key('passwd'):
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

def autotest_request(obj):
	tmp = {}
	config = {}

	config['ip'] = obj.ip 
	config['mac'] = obj.macaddr 
	config['user'] = obj.account
	config['pass'] = obj.passwd 

	tmp['config'] = str(config)
	tmp['token'] = token 

	r = requests.post(url, data=tmp)
	print r.status_code

###################################
# URL API
###################################
@csrf_exempt # for POST requests
def new_autotest_task(req):
	data = []

	plat = req.POST['platform']
	if platform.has_key(plat):
		cameras = Camera.objects.filter(platform = platform[plat])
		for camera in cameras:
			autotest_request(camera)

		return response_ok(data)
	else:
		return response_error('No such platform')

def save_autotest_result(req): 
	# not implement yet
	pass




# vim: tabstop=8 shiftwidth=8 softtabstop=8 noexpandtab
