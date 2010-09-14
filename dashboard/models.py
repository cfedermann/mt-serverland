#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Project: MT Server Land prototype code
 Author: Christian Federmann <cfedermann@dfki.de>
"""
import datetime
import logging
import socket
import uuid
import xmlrpclib

from base64 import b64decode, b64encode
from django.db import models
from django.contrib.auth.models import User
from google.protobuf.message import DecodeError
from os import getcwd
from serverland.settings import LOG_LEVEL, LOG_HANDLER
from serverland.protobuf.TranslationRequestMessage_pb2 import \
  TranslationRequestMessage

# Setup logging support.
logging.basicConfig(level=LOG_LEVEL)
LOGGER = logging.getLogger('serverland.views')
LOGGER.addHandler(LOG_HANDLER)

# Serialized message files will be stored in this location.
TRANSLATION_MESSAGE_PATH = '{0}/messages'.format(getcwd())


class WorkerServer(models.Model):
    """A Worker Server implements translation functionality via XML-RPC."""
    shortname = models.CharField(max_length=50)
    description = models.TextField()
    hostname = models.CharField(max_length=200)
    port = models.CharField(max_length=5)

    def __unicode__(self):
        """Returns a Unicode String representation of the worker server."""
        return self.shortname

    def language_pairs(self):
        """
        Returns a tuple of all supported language pairs for this worker.
        """
        try:
            proxy = xmlrpclib.ServerProxy("{0}:{1}".format(self.hostname,
              self.port))
            return (tuple(x) for x in proxy.language_pairs())

        except (xmlrpclib.Error, socket.error):
            return ()

        return ()

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

    def start_translation(self, serialized):
        """Sends the translation request to the worker server."""
        try:
            proxy = xmlrpclib.ServerProxy("{0}:{1}".format(self.hostname,
              self.port))
            return proxy.start_translation(b64encode(serialized))

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


def create_request_id():
    """Creates a random UUID-4 32-digit hex number for use as request id."""
    new_id = uuid.uuid4().hex
    while (TranslationRequest.objects.filter(request_id=new_id)):
        new_id = uuid.uuid4().hex

    return new_id


class TranslationRequest(models.Model):
    """A Translation Request encodes the parameters of a translation job."""
    shortname = models.CharField(max_length=50)
    request_id = models.CharField(max_length=32, default=create_request_id)
    worker = models.ForeignKey(WorkerServer, related_name='requests')
    owner = models.ForeignKey(User, related_name='requests')
    created = models.DateTimeField(default=datetime.datetime.now)

    # We use a TranslationRequestMessage instance to store all request data.
    # The serialized, binary message will be stored as $request_id.message.

    # Cache attributes that save the request's "state" inside the Django DB.
    ready = models.BooleanField(default=False)
    deleted = models.BooleanField(default=False)

    def __unicode__(self):
        """Returns a Unicode String representation of the request."""
        return u"{0} (request_id={1}, worker={2})".format(self.shortname,
          self.request_id, self.worker.id)

    def is_ready(self):
        """Checks if the current translation request is finished."""
        if not self.ready:
            self.ready = self.worker.is_ready(self.request_id)
            self.save()

            # If the translation request has been finished by now, we fetch
            # the corresponding TranslationRequestMessage from the worker
            # server and copy it to the broker's TRANSLATION_MESSAGE_PATH.
            if self.ready:
                LOGGER.info('Fetching translation result for request' \
                  ' "{0}"'.format(self.request_id))
                serialized = self.worker.fetch_translation(self.request_id)
                handle = open('{0}/{1}.message'.format(
                  TRANSLATION_MESSAGE_PATH, self.request_id), 'w+b')
                handle.write(serialized)
                handle.close()

                # Now that we have successfully retrieved the translation from
                # the worker server, we can delete it from the worker's queue.
                success = self.worker.delete_translation(self.request_id)

                if not success:
                    LOGGER.warning('Could not delete request "{0}" on ' \
                      ' worker "{1}".'.format(self.request_id,
                      self.worker.shortname))

        return self.ready

    def is_corrupted(self):
        """Checks whether the translation request message file is OK."""
        try:
            # Read in serialized message from file.
            handle = open('{0}/{1}.message'.format(TRANSLATION_MESSAGE_PATH,
              self.request_id), 'rb')
            message = handle.read()
            handle.close()

            # Try to create TranslationRequestMessage object from String.
            instance = TranslationRequestMessage()
            instance.ParseFromString(message)
            instance = None

        except (IOError, DecodeError):
            return True

        return False

    def is_valid(self):
        """Checks if the current translation request is valid."""
        return self.worker.is_valid(self.request_id)

    def start_translation(self):
        """Sends the serialized translation request to the worker server."""
        handle = open('{0}/{1}.message'.format(TRANSLATION_MESSAGE_PATH,
          self.request_id), 'rb')
        message = handle.read()
        handle.close()

        return self.worker.start_translation(message)

    def fetch_translation(self):
        """Fetches the TranslationRequestMessage object if ready."""
        if not self.is_ready():
            return "NOT_READY"

        try:
            handle = open('{0}/{1}.message'.format(TRANSLATION_MESSAGE_PATH,
              self.request_id), 'rb')
            serialized = handle.read()
            handle.close()

            message = TranslationRequestMessage()
            message.ParseFromString(serialized)

        except (IOError, DecodeError):
            return "ERROR"

        return message

    def delete_translation(self):
        """Deletes a translation request from the broker server queue."""
        if not self.deleted:
            self.deleted = True
            self.save()

            # If the translation request is not yet ready, we have to ensure
            # that it is properly deleted from the worker's job queue.
            if not self.ready:
                success = self.worker.delete_translation(self.request_id)

                if not success:
                    LOGGER.warning('Could not delete request "{0}" on ' \
                      ' worker "{1}".'.format(self.request_id,
                      self.worker.shortname))

        return self.deleted
