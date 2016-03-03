from ynm.models import Camera, Report
from django.shortcuts import render
from django.http import HttpResponse
import json

# Create your views here.
def camera(req):
	cameras = Camera.objects.all()
	return render(req, 'ynm/camera.html', {'cameras': cameras})
	#return HttpResponse("Hello, world. You're at the camera index.")

def register(req):
	data = []

	add_camera(req.GET)
	cameras = Camera.objects.all()
	for camera in cameras:
		tmp = fill_camera_data(camera)
		data.append(tmp)
	
	return response_ok(data) 

def report(req):
	data = []

	if 'name' in req.GET:
		reports = Report.objects.filter(camera__maintainer__icontains = req.GET['name']).order_by('name')
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

def add_camera(obj):
	camera = Camera()
	camera.maintainer = obj['maintainer'] 
	camera.modelname= obj['modelname'] 
	camera.macaddr= obj['macaddr'] 
	camera.save()

def fill_camera_data(obj):
	tmp = {}

	tmp['maintainer'] = obj.maintainer
	tmp['modelname'] = obj.modelname
	tmp['macaddr'] = obj.macaddr

	return tmp

def fill_report_data(obj):
	tmp = {}

	tmp['id'] =obj.id
	tmp['name'] = obj.name
	tmp['time'] = obj.time.strftime("%Y-%m-%d %H:%M:%S")
	tmp['maintainer'] = obj.camera.maintainer

	print tmp
	return tmp


# vim: tabstop=8 shiftwidth=8 softtabstop=8 noexpandtab
