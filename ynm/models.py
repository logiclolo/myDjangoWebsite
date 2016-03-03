from django.db import models

# Create your models here.
class Camera(models.Model):
	maintainer = models.CharField(max_length = 16)
	macaddr = models.CharField(max_length = 16)
	modelname = models.CharField(max_length = 16)

	def __unicode__(self):
		return self.maintainer

class Report(models.Model):
	name = models.CharField(max_length = 128)
	camera = models.ForeignKey(Camera)
	time = models.DateTimeField('date generated')
	content = models.FileField()

	def __unicode__(self):
		return self.name

# vim: tabstop=8 shiftwidth=8 softtabstop=8 noexpandtab
