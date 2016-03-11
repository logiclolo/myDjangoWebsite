from django.conf.urls import patterns, url

urlpatterns = patterns('ynm.views',
    url(r'^register/$', 'register'),
    url(r'^report/$', 'report'),
    url(r'^camera/$', 'camera'),
    url(r'^update/$', 'update'),
)

