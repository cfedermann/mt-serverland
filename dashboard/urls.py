"""
Project: MT Server Land prototype code
 Author: Christian Federmann <cfedermann@dfki.de>
"""
from django.conf.urls.defaults import patterns, include

urlpatterns = patterns('serverland.dashboard.views',
  (r'^$', 'dashboard'),
  (r'^create/$', 'create'),
  (r'^delete/(?P<request_id>[a-f0-9]{32})/$', 'delete'),
  (r'^result/(?P<request_id>[a-f0-9]{32})/$', 'result'),
  (r'^download/(?P<request_id>[a-f0-9]{32})/$', 'download'),
  (r'^api/', include('serverland.dashboard.api.urls')),
)
