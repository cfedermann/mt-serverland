"""
Project: MT Server Land
 Author: Will Roberts <William.Roberts@dfki.de>

URL resources for the serverland dashboard Web API.

"""

from django.conf.urls.defaults import patterns, url
from piston.resource import Resource
from serverland.dashboard.api.handlers import RequestHandler, WorkerHandler
from serverland.dashboard.api.authentication import TokenAuthentication

# TODO: check if this import is actually required?!
import serverland.dashboard.api.protobuf_emitter

AUTH = TokenAuthentication()

REQUEST_HANDLER = Resource(RequestHandler, authentication=AUTH)
WORKER_HANDLER = Resource(WorkerHandler, authentication=AUTH)

urlpatterns = patterns(
    '',
    url(r'^((?P<emitter_format>[^/]+)/)?requests/((?P<shortname>[^/]+)/)?$',
        REQUEST_HANDLER, {'results': False}, name='requests'),
    url(r'^((?P<emitter_format>[^/]+)/)?results/((?P<shortname>[^/]+)/)?$',
        REQUEST_HANDLER, {'results': True}, name='results'),
    url(r'^((?P<emitter_format>[^/]+)/)?workers/((?P<shortname>[^/]+)/)?$',
        WORKER_HANDLER)
    )
