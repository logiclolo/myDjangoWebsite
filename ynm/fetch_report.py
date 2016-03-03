from django.core.files import File
from .models import Report
from django.utils import timezone

reopen = open('/home/deploy/django/myDjangoWebsite/media/report/new2.txt', 'r')
django_file = File(reopen)

report = Report()
report.name
report.camera
report.time = timezone.now()
report.content.save('new.txt', django_file, save=True)
