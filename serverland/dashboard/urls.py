"""
Project: MT Server Land
 Author: Christian Federmann <cfedermann@dfki.de>
"""
from django.conf.urls.defaults import patterns, include, url

urlpatterns = patterns('serverland.dashboard.views',
  url(r'^$', 'dashboard', name='dashboard'),
  url(r'^create/$', 'create', name='create'),
  url(r'^delete/(?P<request_id>[a-f0-9]{32})/$', 'delete', name='delete'),
  url(r'^result/(?P<request_id>[a-f0-9]{32})/$', 'result', name='result'),
  url(r'^download/(?P<request_id>[a-f0-9]{32})/$', 'download',
    name='download'),
  url(r'^api/', include('serverland.dashboard.api.urls')),
)
