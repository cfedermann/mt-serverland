"""
Project: MT Server Land prototype code
 Author: Christian Federmann <cfedermann@dfki.de>
"""
import logging
import socket

from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from serverland.dashboard.models import TranslationRequest, WorkerServer
from serverland.dashboard.models import TRANSLATION_MESSAGE_PATH
from serverland.dashboard.forms import TranslationRequestForm
from serverland.settings import LOG_LEVEL, LOG_HANDLER, DEPLOYMENT_PREFIX
from serverland.protobuf.TranslationRequestMessage_pb2 import \
  TranslationRequestMessage

# Setup logging support.
logging.basicConfig(level=LOG_LEVEL)
LOGGER = logging.getLogger('dashboard.views')
LOGGER.addHandler(LOG_HANDLER)

@login_required
def dashboard(request):
    """
    Renders the MT Server Land dashboard for the current user.

    Does not yet work for anonymous users!
    """
    LOGGER.info('Rendering dashboard for user "{0}".'.format(
      request.user.username))

    socket.setdefaulttimeout(0.2)

    ordered = TranslationRequest.objects.all().order_by('-created')
    filtered = ordered.filter(owner=request.user)
    requests = [r for r in filtered if not r.deleted]
    finished = [r for r in requests if r.is_ready()]
    invalid = [r for r in requests if not r.is_valid() and not r in finished]
    active = [r for r in requests if not r in finished and not r in invalid]

    dictionary = {'title': 'MT Server Land (prototype) -- Dashboard',
      'PREFIX': DEPLOYMENT_PREFIX, 'finished_requests': finished,
      'active_requests': active, 'invalid_requests': invalid}
    return render_to_response('dashboard/dashboard.html', dictionary,
      context_instance=RequestContext(request))

@login_required
def create(request):
    """
    Creates a new translation request for the current user.

    Does not yet work for anonymous users!
    """
    LOGGER.info('Rendering create request view for user "{0}".'.format(
      request.user.username))

    form = None

    if request.method == "POST":
        form = TranslationRequestForm(request.user, request.POST,
          request.FILES)

        if form.errors:
            LOGGER.info('Form validation errors: {0}'.format(
              ['{0}: {1}'.format(a, b[0]) for a, b in form.errors.items()]))

        if form.is_valid():
            LOGGER.info('Create request form is valid.')

            new = TranslationRequest()
            new.shortname = request.POST['shortname']
            new.owner = request.user
            new.worker = WorkerServer.objects.get(
              pk=int(request.POST['worker']))

            message = TranslationRequestMessage()
            message.request_id = new.request_id
            message.source_language = request.POST['source_language']
            message.target_language = request.POST['target_language']
            message.source_text = u''
            for chunk in request.FILES['source_text'].chunks():
                message.source_text += unicode(chunk, 'utf-8')

            handle = open('{0}/{1}.message'.format(TRANSLATION_MESSAGE_PATH,
              new.request_id), 'w+b')
            handle.write(message.SerializeToString())
            handle.close()

            new.save()

            # cfedermann: We have to decide whether the translation process
            #   should directly be sent to the worker server or whether it
            #   makes more sense to "queue" it on the broker server and have
            #   a cronjob start the process when the worker is not busy...
            #   This does have impact on system performance/robustness!
            new.start_translation()

            messages.add_message(request, messages.SUCCESS, 'Successfully ' \
              'started translation request "{0}".'.format(new.shortname))
            return HttpResponseRedirect('{0}/dashboard/'.format(
              DEPLOYMENT_PREFIX))

    else:
        form = TranslationRequestForm(user=request.user)

    #from serverland.dashboard.models import WorkerServer
    #workers = WorkerServer.objects.all()
    #active_workers = [w for w in workers if w.is_alive()]

    dictionary = {'title': 'MT Server Land (prototype) -- Create translation',
      'PREFIX': DEPLOYMENT_PREFIX, 'form': form}
    return render_to_response('dashboard/create.html', dictionary,
      context_instance=RequestContext(request))

@login_required
def delete(request, request_id):
    """
    Deletes a translation request.
    """
    req = get_object_or_404(TranslationRequest, request_id=request_id)

    if req.owner != request.user:
        LOGGER.warning('Illegal delete request from user "{0}".'.format(
          request.user.username or "Anonymous"))

        return HttpResponseRedirect('{0}/dashboard/'.format(
          DEPLOYMENT_PREFIX))

    LOGGER.info('Deleting translation request "{0}" for user "{1}".'.format(
      request_id, request.user.username or "Anonymous"))
    req.delete_translation()

    messages.add_message(request, messages.SUCCESS, 'Successfully deleted' \
      ' request "{0}".'.format(req.shortname))
    return HttpResponseRedirect('{0}/dashboard/'.format(DEPLOYMENT_PREFIX))

@login_required
def result(request, request_id):
    """
    Returns the result of a translation request.
    """
    req = get_object_or_404(TranslationRequest, request_id=request_id)

    if req.owner != request.user:
        LOGGER.warning('Illegal result request from user "{0}".'.format(
          request.user.username or "Anonymous"))

        return HttpResponseRedirect('{0}/dashboard/'.format(
          DEPLOYMENT_PREFIX))

    # cfedermann: Make sure that the request is marked as finished once the
    #   result has been transferred to the local hard disk!!!  We are trying
    #   to access the result from the worker server for each request now :(
    #   This will break if the worker server has forgotten about the request.
    LOGGER.info('Fetching request "{0}" for user "{1}".'.format(
      request_id, request.user.username or "Anonymous"))
    translation_message = req.fetch_translation()
    translation_result = translation_message
    translation_packet_data = None

    if type(translation_result) == TranslationRequestMessage:
        translation_result = translation_message.target_text
        translation_packet_data = [(x.key, x.value) for x in 
          translation_message.packet_data]

    dictionary = {'title': 'MT Server Land (prototype) -- {0}'.format(
      req.shortname), 'request': req, 'result': translation_result,
      'packet_data': translation_packet_data, 'PREFIX': DEPLOYMENT_PREFIX}
    return render_to_response('dashboard/result.html', dictionary,
      context_instance=RequestContext(request))

@login_required
def download(request, request_id):
    """
    Downloads the result of a translation request.
    """
    req = get_object_or_404(TranslationRequest, request_id=request_id)

    if req.owner != request.user:
        LOGGER.warning('Illegal download request from user "{0}".'.format(
          request.user.username or "Anonymous"))

        return HttpResponseRedirect('{0}/dashboard/'.format(
          DEPLOYMENT_PREFIX))

    LOGGER.info('Downloading request "{0}" for user "{1}".'.format(
      request_id, request.user.username or "Anonymous"))

    # We only return the target text, not the full TranslationRequestMessage.
    translation = req.fetch_translation().target_text.encode('utf-8')
    
    # We return it as a "text/plain" file attachment with charset "UTF-8".
    response = HttpResponse(translation, mimetype='text/plain; charset=UTF-8')
    response['Content-Disposition'] = 'attachment; filename="{0}.txt"'.format(
      req.shortname)
    return response
