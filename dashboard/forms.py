"""
Project: MT Server Land prototype code
 Author: Christian Federmann <cfedermann@dfki.de>
"""
import logging
import socket
import subprocess

from os import remove
from django.forms import ModelForm, ValidationError, FileField
from serverland.dashboard.models import TranslationRequest
from serverland.settings import LOG_LEVEL, LOG_HANDLER

# Setup logging support.
logging.basicConfig(level=LOG_LEVEL)
LOGGER = logging.getLogger('dashboard.forms')
LOGGER.addHandler(LOG_HANDLER)

class TranslationRequestForm(ModelForm):
    """Form class for a translation request object."""
    class Meta:
        """Meta class that connects to the TranslationRequest class."""
        model = TranslationRequest
        exclude = ('request_id', 'owner', 'created', 'ready', 'deleted')
    
    # We add a FileField widget to allow uploading of the source text.
    source_text = FileField()
    
    def clean_shortname(self):
        """Checks that the new shortname is not yet in use."""
        data = self.cleaned_data['shortname']
        LOGGER.debug('clean_shortname() called with shortname="{0}".'.format(
          data))
        
        try:
            active_requests = TranslationRequest.objects.filter(deleted=False)
            other_request = active_requests.filter(shortname=data)
            assert(other_request.count() == 0)
        
        except AssertionError:
            raise ValidationError("The chosen shortname is already in use.")
        
        return data
    
    def clean_worker(self):
        """Checks that the chosen worker server is up an running."""
        data = self.cleaned_data['worker']
        LOGGER.debug('clean_worker() called for worker"{0}".'.format(
          data.shortname))
        
        try:
            assert(data.is_alive())
        
        except (socket.error, AssertionError):
            raise ValidationError("The chosen worker server is not running.")
        
        return data
    
    def clean_source_text(self):
        """Validates the source text field, verifies that it contains text."""
        data = self.cleaned_data['source_text']
        LOGGER.debug('clean_source_text() called for file "{0}".'.format(
          data.name))
        
        destination = open('/tmp/{0}'.format(data.name), 'w+b')
        for chunk in data.chunks():
            destination.write(chunk)
        destination.close()

        # Instead of using /usr/bin/file directly, we could use libmagic:
        # - http://github.com/ahupp/python-magic
        LOGGER.debug('TODO: use libmagic instead of "file" call!')
        mime_type = subprocess.Popen('/usr/bin/file --mime /tmp/{0}'.format(
          data.name), shell=True, stdout=subprocess.PIPE).communicate()[0]
        mime_type = mime_type.strip().split()[1].strip(';')
        LOGGER.info('Detected MIME type "{0}" for file "{1}".'.format(
          mime_type, data.name))
        
        remove('/tmp/{0}'.format(data.name))
        
        if mime_type != "text/plain":
            raise ValidationError("You can only upload text files.")

        return data