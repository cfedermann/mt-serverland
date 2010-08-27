'''
Web API handlers for the serverland dashboard.
Project: MT Server Land prototype code
 Author: Will Roberts <William.Roberts@dfki.de>

'''

from django.contrib import messages
from django.core.urlresolvers import reverse
from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist
from django.shortcuts import get_object_or_404
from piston.handler import BaseHandler
from piston.utils import rc
from serverland.dashboard.models import WorkerServer, TranslationRequest
from serverland.dashboard.models import TRANSLATION_MESSAGE_PATH
from serverland.dashboard.forms import TranslationRequestForm
from serverland.workers.TranslationRequestMessage_pb2 import \
     TranslationRequestMessage
import uuid

class RequestHandler(BaseHandler):
    '''API handler for translation request queries.'''

    # we don't allow updating translation requests
    allowed_methods = ('GET', 'POST', 'DELETE')

    def read(self, request, shortname = None, results = False):
        '''Handles a GET request asking about translation requests.'''
        not_deleted = TranslationRequest.objects.exclude(deleted = True)
        not_deleted = not_deleted.filter(owner = request.user)
        if shortname is None:
            objects = not_deleted.all()
        else:
            try:
                _request_uuid = uuid.UUID(shortname)
                objects = [get_object_or_404(not_deleted, request_id=shortname)]
            except ValueError:
                objects = [get_object_or_404(not_deleted, shortname=shortname)]
        objects = [ RequestHandler.request_to_dict(o, results)
                    for o in objects ]
        if len(objects) == 1:
            objects = objects[0]
        return objects

    def create(self, request, shortname = None, results = False):
        '''Handles a POST request to create a new translation request.'''
        if shortname is not None or results:
            return rc.BAD_REQUEST
        print 'CREATE content-type', request.content_type # DEBUG
        # get the data from the POST request
        postdata = self.flatten_dict(request.data)
        # ensure that the worker field is present
        postdata['worker'] = postdata.get('worker','')
        # convert worker shortname to a worker ID if needed
        if not postdata['worker'].isdigit():
            try:
                postdata['worker'] = str(WorkerServer.objects.get(
                    shortname=postdata['worker']).id)
            except ObjectDoesNotExist:
                return rc.BAD_REQUEST
        # check whether the translation request is a duplicate
        if 'shortname' in postdata:
            try:
                TranslationRequest.objects.get(shortname=postdata['shortname'])
                return rc.DUPLICATE_ENTRY
            except MultipleObjectsReturned:
                return rc.DUPLICATE_ENTRY
            except ObjectDoesNotExist:
                pass
        # validate POST data using our Django form
        form = TranslationRequestForm(postdata, request.FILES)
        try:
            if not form.is_valid():
                return rc.BAD_REQUEST
        except KeyError:
            return rc.BAD_REQUEST
        # create a new request object
        new = TranslationRequest()
        new.shortname = form.cleaned_data['shortname']
        new.owner = request.user
        new.worker = form.cleaned_data['worker']
        # create a new worker message
        message = TranslationRequestMessage()
        message.request_id = new.request_id
        message.source_language = form.cleaned_data['source_language']
        message.target_language = form.cleaned_data['target_language']
        message.source_text = u''
        for chunk in request.FILES['source_text'].chunks():
            message.source_text += unicode(chunk, 'utf-8')

        handle = open('{0}/{1}.message'.format(TRANSLATION_MESSAGE_PATH,
                                               new.request_id), 'w+b')
        handle.write(message.SerializeToString())
        handle.close()

        new.save()
        new.start_translation()

        messages.add_message(request, messages.SUCCESS, 'Successfully ' \
                             'started translation request "{0}".'.format(
                                new.shortname))
        # return 201 CREATED
        response = rc.CREATED
        # put the URI of the newly created object into the HTTP header
        # Location field (see RFC 2616)
        response['Location'] = reverse('requests', args=[new.request_id + '/'])
        # echo the created object inside the HTTP response
        # NOTE: this overwrites the "Location" header field set above.
        # See piston.resource.__call__()
        response.content = RequestHandler.request_to_dict(new)
        return response

    def delete(self, request, shortname = None, results = False):
        '''Handles a DELETE request to destroy a translation request.'''
        #print 'delete' # DEBUG
        if shortname is None or results:
            return rc.BAD_REQUEST
        not_deleted = TranslationRequest.objects.exclude(deleted = True)
        not_deleted = not_deleted.filter(owner = request.user)
        try:
            try:
                _request_uuid = uuid.UUID(shortname)
                req = not_deleted.get(request_id=shortname)
            except ValueError:
                req = not_deleted.get(shortname=shortname)
        except MultipleObjectsReturned:
            return rc.DUPLICATE_ENTRY
        except ObjectDoesNotExist:
            return rc.NOT_HERE

        req.delete_translation()

        messages.add_message(request, messages.SUCCESS, 'Successfully deleted' \
                             ' request "{0}".'.format(req.shortname))
        return rc.DELETED

    @staticmethod
    def request_to_dict ( request, include_results = False ):
        '''Transforms a TranslationRequest object to a Python
        dictionary.'''
        retval = {}
        retval['owner'] = request.owner.username
        retval['shortname'] = request.shortname
        retval['worker'] = request.worker.shortname
        retval['created'] = request.created
        retval['request_id'] = request.request_id
        retval['ready'] = request.is_ready()
        if include_results:
            translation_message = request.fetch_translation()
            if type(translation_message) == TranslationRequestMessage:
                retval['result'] = translation_message.target_text
                retval.update( [(x.key, x.value) for x in
                                translation_message.packet_data] )
            else:
                retval['result'] = translation_message
        return retval

class WorkerHandler(BaseHandler):
    '''API handler for worker server queries.'''

    # workers are read-only accessible
    allowed_methods = ('GET',)

    def read(self, request, shortname = None):
        '''Handles a GET request asking about worker servers.'''
        if shortname is None:
            objects = WorkerServer.objects.all()
        else:
            objects = [get_object_or_404(WorkerServer, shortname=shortname)]
        objects = [ WorkerHandler.server_to_dict(o) for o in objects ]
        if len(objects) == 1:
            objects = objects[0]
        return objects

    @staticmethod
    def server_to_dict ( server ):
        '''Transforms a WorkerServer object to a Python dictionary.'''
        retval = {}
        retval['shortname'] = server.shortname
        retval['description'] = server.description
        retval['is_alive'] = server.is_alive()
        if retval['is_alive']:
            retval['is_busy'] = server.is_busy()
            retval['language_pairs'] = [ x for x in server.language_pairs() ]
        return retval

