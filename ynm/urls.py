from django.conf.urls import patterns, url

urlpatterns = patterns('ynm.views',
    url(r'^register/$', 'register'),
    url(r'^report/$', 'report'),
    url(r'^camera/$', 'camera'),
    url(r'^update/$', 'update'),
    url(r'^onefw-web-autotest-task/$', 'new_autotest_task'),
    url(r'^onefw-web-autotest-result/$', 'save_autotest_result'),
)

