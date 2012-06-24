"""
Baseline implementation for a MT Server Land "worker" server.

Implements the basic "worker" interface.
"""
import logging
import stat

from base64 import b64encode, b64decode
from google.protobuf.message import DecodeError
from logging.handlers import RotatingFileHandler
from multiprocessing import Process
from os import chmod, remove, popen
from time import sleep
from random import random
from SimpleXMLRPCServer import SimpleXMLRPCServer

from protobuf.TranslationRequestMessage_pb2 import TranslationRequestMessage


class AbstractWorkerServer(object):
    """
    Abstract worker server defining the basic worker server interface.
    """
    __name__ = 'AbstractWorkerServer'

    finished = False
    server = None
    jobs = {}

    def __init__(self, host, port, logfile, min_memory=None):
        """
        Creates a new WorkerServer instance serving from host:port.
        """
        LOG_LEVEL = logging.DEBUG
        LOG_FILENAME = logfile
        LOG_FORMAT = '[%(asctime)s] %(name)s::%(levelname)s %(message)s'
        LOG_DATE = '%m/%d/%Y @ %H:%M:%S'
        LOG_FORMATTER = logging.Formatter(LOG_FORMAT, LOG_DATE)

        LOG_HANDLER = RotatingFileHandler(filename=LOG_FILENAME, mode='a',
          maxBytes=1024*1024, backupCount=5, encoding='utf-8')
        LOG_HANDLER.setLevel(LOG_LEVEL)
        LOG_HANDLER.setFormatter(LOG_FORMATTER)

        logging.basicConfig(level=LOG_LEVEL)
        self.LOGGER = logging.getLogger(self.__name__)
        self.LOGGER.addHandler(LOG_HANDLER)
        
        # Change permissions of logfile so that everybody may read and write.
        mode = stat.S_IREAD | stat.S_IWRITE
        mode |= stat.S_IRGRP | stat.S_IWGRP
        mode |= stat.S_IROTH | stat.S_IWOTH
        chmod(LOG_FILENAME, mode)
        
        self.server = SimpleXMLRPCServer((host, port), allow_none=True)
        self.LOGGER.info("{0} listening on {1}:{2}".format(self.__name__,
          host, port))

        self.jobs = {}

        # Register worker interface functions.
        self.server.register_function(self.stop_worker, "stop_worker")
        self.server.register_function(self.list_requests, "list_requests")
        self.server.register_function(self.is_alive, "is_alive")
        self.server.register_function(self.is_busy, "is_busy")
        self.server.register_function(self.is_ready, "is_ready")
        self.server.register_function(self.is_valid, "is_valid")
        self.server.register_function(self.start_translation,
          "start_translation")
        self.server.register_function(self.fetch_translation,
          "fetch_translation")
        self.server.register_function(self.delete_translation,
          "delete_translation")
        self.server.register_function(self.language_pairs, "language_pairs")

    @staticmethod
    def usage():
        """
        Returns usage information, e.g. for additional parameters, etc.
        """
        return ()

    def parse_args(self, args):
        """
        Parses the given args list and sets worker specific paramters.
        """
        return True

    def start_worker(self):
        """
        Starts the event handler of the worker server instance.
        """
        self.LOGGER.info("Started {0} instance, serving via XML-RPC.".format(
          self.__name__))

        while not self.finished:
            self.server.handle_request()

    def stop_worker(self):
        """
        Stops the event handler terminating all pending translation processes.
        """
        self.LOGGER.info('Stopped {0} instance.'.format(self.__name__))
        if not self.finished:
            self.finished = True

            for proc in self.jobs.values():
                if proc.is_alive():
                    proc.terminate()

    def list_requests(self):
        """Returns a list of all registered translation requests."""
        return self.jobs.keys()

    def is_alive(self):
        """
        Will return True to signal that the worker server is running.
        """
        return True

    def is_busy(self):
        """
        Checks if the worker server is currently busy.
        """
        if any([p.is_alive() for p in self.jobs.values()]):
            return True

        return False

    def is_ready(self, request_id):
        """
        Checks if a translation request is finished.

        Returns False if request_id is invalid.
        """
        if not request_id in self.jobs.keys():
            self.LOGGER.info('Unknown request id "{0}" queried.'.format(
              request_id))

            return False

        return not self.jobs[request_id].is_alive()

    def is_valid(self, request_id):
        """
        Checks if a translation request is valid, i.e. known in self.jobs.

        Returns False if request_id is invalid.
        """
        return request_id in self.jobs.keys()

    def start_translation(self, serialized):
        """
        Stores a new translation request with the given id and source text.

        Writes out a serialized version of the TranslationRequestMessage to
        the worker server's output folder.  Returns True if successful, False
        when an error occurs.
        """
        try:
            # Create new TranslationRequestMessage object and load serialized.
            message = TranslationRequestMessage()
            message.ParseFromString(b64decode(serialized))

            # Write serialized translation request message to file.
            handle = open('/tmp/{0}.message'.format(message.request_id), 'w')
            handle.write(message.SerializeToString())
            handle.close()

            self.LOGGER.info('Created new translation request "{0}".'.format(
              message.request_id))

            # Start up translation process for the new request object.
            proc = Process(target=self.handle_translation,
              args=(message.request_id,))
            proc.start()
            self.jobs[message.request_id] = proc
            self.LOGGER.info('Started translation job "{0}"'.format(proc))

        except (IOError, DecodeError):
            self.LOGGER.error('Could not start translation job!')

            if message.request_id in self.jobs.keys():
                self.jobs.pop(message.request_id)

            return False

        return True

    def fetch_translation(self, request_id):
        """
        Retrieves translation result for the given request id.

        Returns "ERROR" if request_id is invalid or "NOT_READY" if the
        translation request is not yet ready.
        """
        if not request_id in self.jobs.keys():
            self.LOGGER.info('Unknown request id "{0}" queried.'.format(
              request_id))

            return b64encode("ERROR")

        # Check if the given request is still being processed.
        if self.jobs[request_id].is_alive():
            return b64encode("NOT_READY")

        self.LOGGER.debug("Translation requests: {0}".format(
          repr(self.jobs)))

        try:
            handle = open('/tmp/{0}.message'.format(request_id), 'rb')
            message = TranslationRequestMessage()
            message.ParseFromString(handle.read())
            handle.close()

            return b64encode(message.SerializeToString())

        except (IOError, DecodeError):
            return b64encode("ERROR")

        return b64encode("ERROR")

    def delete_translation(self, request_id):
        """
        Deletes a translation request from the worker server.

        Returns True if the translation request could be deleted successfully.
        """
        if not request_id in self.jobs.keys():
            self.LOGGER.info('Unknown request id "{0}" queried.'.format(
              request_id))

            return False

        self.jobs[request_id].terminate()
        self.LOGGER.info('Terminated request "{0}".'.format(request_id))

        remove('/tmp/{0}.message'.format(request_id))
        return True

    def handle_translation(self, request_id):
        """
        Raises NotImplemented exception, has to be implemented in sub-classes.
        """
        raise NotImplementedError

    def language_pairs(self):
        """
        Returns a tuple of all supported language pairs for this worker.
        """
        raise NotImplementedError

    def language_code(self, iso639_2_code):
        """
        Converts a given ISO-639-2 code into the worker representation.

        Returns None for unknown languages.
        """
        raise NotImplementedError


class DummyWorker(AbstractWorkerServer):
    """
    Implements a dummy worker server that blocks for a random interval and
    then writes out an all-uppercase "translation" of the input text.
    """
    __name__ = "DummyWorker"

    def handle_translation(self, request_id):
        """
        Dummy translation handler that blocks for a random amount of time.

        Returns all-uppercase version of Text as translation.
        """
        # Block up to 100 seconds...
        interval = 50 + int(random() * 100)
        self.LOGGER.info("Sleeping for {0} seconds...".format(interval))
        sleep(interval)

        # The dummy implementation takes the source text from /tmp/$id.source
        # and writes an upper-cased version of that text to /tmp/$id.target.

        self.LOGGER.debug("Finalizing result for request {0}".format(
          request_id))

        handle = open('/tmp/{0}.message'.format(request_id), 'r+b')
        message = TranslationRequestMessage()
        message.ParseFromString(handle.read())
        message.target_text = message.source_text.upper()
        handle.seek(0)
        handle.write(message.SerializeToString())
        handle.close()
