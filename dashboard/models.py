#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Project: MT Server Land prototype code
 Author: Christian Federmann <cfedermann@dfki.de>
"""
import datetime
import logging
import socket
import xmlrpclib
from base64 import b64decode, b64encode
from django.db import models
from django.contrib.auth.models import User
from serverland.settings import LOG_LEVEL, LOG_HANDLER

# Setup logging support.
logging.basicConfig(level=LOG_LEVEL)
LOGGER = logging.getLogger('serverland.views')
LOGGER.addHandler(LOG_HANDLER)


class WorkerServer(models.Model):
    """A Worker Server implements translation functionality via XML-RPC."""
    shortname = models.CharField(max_length=50)
    description = models.TextField()
    source_language = models.CharField(max_length=3)
    target_language = models.CharField(max_length=3)
    hostname = models.CharField(max_length=200)
    port = models.CharField(max_length=5)
    
    def __unicode__(self):
        """Returns a Unicode String representation of the worker server."""
        return u"{0} ({1}→{2})".format(self.shortname, self.source_language,
          self.target_language)

    def is_alive(self):
        """Checks if the current worker server instance is alive."""
        try:
            proxy = xmlrpclib.ServerProxy("{0}:{1}".format(self.hostname,
              self.port))
            return proxy.is_alive()

        except (xmlrpclib.Error, socket.error):
            return False

        return False

    def is_busy(self):
        """Checks if the current worker server instance is busy."""
        try:
            proxy = xmlrpclib.ServerProxy("{0}:{1}".format(self.hostname,
              self.port))
            return proxy.is_busy()

        except (xmlrpclib.Error, socket.error):
            return False

        return False

    def is_ready(self, request_id):
        """Checks if the specified request is finished."""
        try:
            proxy = xmlrpclib.ServerProxy("{0}:{1}".format(self.hostname,
              self.port))
            return proxy.is_ready(request_id)

        except (xmlrpclib.Error, socket.error):
            return False

        return False

    def is_valid(self, request_id):
        """Checks if the specified request is valid."""
        try:
            proxy = xmlrpclib.ServerProxy("{0}:{1}".format(self.hostname,
              self.port))
            return proxy.is_valid(request_id)

        except (xmlrpclib.Error, socket.error) as inst:
            print type(inst)
            print inst.args
            print inst
            return False

        return False


    def start_translation(self, request_id, text):
        """Sends the translation request to the worker server."""
        try:
            proxy = xmlrpclib.ServerProxy("{0}:{1}".format(self.hostname,
              self.port))
            text = b64encode(text)
            return proxy.start_translation(request_id, text)
        
        except (xmlrpclib.Error, socket.error):
            return None
        
        return None

    def fetch_translation(self, request_id):
        """Fetches a translation result for the given request_id."""
        try:
            proxy = xmlrpclib.ServerProxy("{0}:{1}".format(self.hostname,
              self.port))
            return b64decode(proxy.fetch_translation(request_id))

        except (xmlrpclib.Error, socket.error):
            return "ERROR"

        return "ERROR"

    def delete_translation(self, request_id):
        """Deletes a translation request with the given request_id."""
        try:
            proxy = xmlrpclib.ServerProxy("{0}:{1}".format(self.hostname,
              self.port))
            return proxy.delete_translation(request_id)

        except (xmlrpclib.Error, socket.error):
            return False

        return False

class TranslationRequest(models.Model):
    """A Translation Request encodes the parameters of a translation job."""
    shortname = models.CharField(max_length=50)
    worker = models.ForeignKey(WorkerServer, related_name='requests')
    source_text = models.FileField(upload_to='requests')
    request_id = models.CharField(max_length=32, editable=False, blank=True)
    created = models.DateTimeField(editable=False,
      default=datetime.datetime.now)
    owner = models.ForeignKey(User, related_name='requests', editable=False)
    
    # Cache attributes that save the request's "state" inside the Django DB.
    ready = models.BooleanField(editable=False, default=False)
    deleted = models.BooleanField(editable=False, default=False)
    result = models.TextField(editable=False, default="")
    
    def __unicode__(self):
        """Returns a Unicode String representation of the request."""
        return u"{0} (request_id={1}, worker={2})".format(self.shortname,
          self.request_id, self.worker.id)

    def is_ready(self):
        """Checks if the current translation request is finished."""
        if not self.ready:
            self.ready = self.worker.is_ready(self.request_id)
            self.save()

        return self.ready

    def is_valid(self):
        """Checks if the current translation request is valid."""
        return self.worker.is_valid(self.request_id)

    def start_translation(self):
        """Sends the translation request to the associated worker server."""
        return self.worker.start_translation(self.request_id,
          self.source_text.read())

    def fetch_translation(self):
        """Fetches a translation result from the worker server."""
        if self.result == "":
            self.result = self.worker.fetch_translation(self.request_id)
            
            if self.result == "ERROR":
                LOGGER.warning('Could not fetch translation for request' \
                  ' "{0}" from worker "{1}".'.format(self.request_id,
                  self.worker.shortname))
            
            self.save()

        return self.result

    def delete_translation(self):
        """Kills and deletes a translation request from the worker server."""
        if not self.deleted:
            self.deleted = self.worker.delete_translation(self.request_id)
            
            if not self.deleted:
                LOGGER.warning('Could not delete request "{0}" on worker' \
                  ' "{1}".'.format(self.request_id, self.worker.shortname))
                
                self.deleted = True
            
            self.save()

        return self.deleted
