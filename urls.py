"""
Project: MT Server Land prototype code
 Author: Christian Federmann <cfedermann@dfki.de>
"""
from django.conf.urls.defaults import patterns, include
from django.contrib import admin
from serverland.settings import MEDIA_ROOT

admin.autodiscover()

urlpatterns = patterns('',
  (r'^$', 'serverland.views.frontpage'),
  (r'^login/$', 'serverland.views.login'),
  (r'^logout/$', 'serverland.views.logout',
    {'next_page': '/'}),
  
  (r'^dashboard/', include('serverland.dashboard.urls')),
  
  (r'^site_media/(?P<path>.*)$', 'django.views.static.serve',
    {'document_root': MEDIA_ROOT}),
  
  (r'^admin/', include(admin.site.urls)),
)
