"""
URL resources for the serverland dashboard Web API.
Project: MT Server Land prototype code
 Author: Will Roberts <William.Roberts@dfki.de>
"""

from django.conf.urls.defaults import patterns, url
from piston.resource import Resource
from serverland.dashboard.api.handlers import RequestHandler, WorkerHandler
from serverland.dashboard.api.authentication import TokenAuthentication

auth = TokenAuthentication()

request_handler = Resource(RequestHandler, authentication=auth)
worker_handler = Resource(WorkerHandler, authentication=auth)

urlpatterns = patterns(
    '',
    url(r'^((?P<emitter_format>[^/]+)/)?requests/((?P<shortname>[^/]+)/)?$',
        request_handler, {'results': False}, name='requests'),
    url(r'^((?P<emitter_format>[^/]+)/)?results/((?P<shortname>[^/]+)/)?$',
        request_handler, {'results': True}, name='results'),
    url(r'^((?P<emitter_format>[^/]+)/)?workers/((?P<shortname>[^/]+)/)?$',
        worker_handler)
    )
