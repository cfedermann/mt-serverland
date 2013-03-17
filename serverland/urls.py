"""
Project: MT Server Land
 Author: Christian Federmann <cfedermann@dfki.de>
"""
from django.conf.urls.defaults import patterns, include, url
from django.contrib import admin
from serverland.settings import DEBUG, MEDIA_ROOT, DEPLOYMENT_PREFIX

if not DEBUG:
    # pylint: disable-msg=W0611
    from django.conf.urls.defaults import handler404, handler500

admin.autodiscover()

PREFIX = DEPLOYMENT_PREFIX[1:]

urlpatterns = patterns('',
  url(r'^{0}/$'.format(PREFIX), 'serverland.views.frontpage',
    name='frontpage'),
  url(r'^{0}/login/$'.format(PREFIX), 'serverland.views.login', name='login'),
  url(r'^{0}/logout/$'.format(PREFIX), 'serverland.views.logout',
    {'next_page': '{0}/'.format(DEPLOYMENT_PREFIX)}, name='logout'),
  
  url(r'^{0}/dashboard/'.format(PREFIX),
    include('serverland.dashboard.urls')),
  
  # TODO: do we actually need this anymore?  We have to move to static files
  #   anyway, so this seems superfluous at the moment...
  (r'^{0}/site_media/(?P<path>.*)$'.format(PREFIX),
    'django.views.static.serve', {'document_root': MEDIA_ROOT}),
  
  (r'^{0}/admin/'.format(PREFIX), include(admin.site.urls)),
)
