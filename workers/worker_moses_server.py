"""
Implementation of a worker server that connects to a Moses SMT server system.
"""
import re
import sys
import xmlrpclib

from workers.worker import AbstractWorkerServer
from protobuf.TranslationRequestMessage_pb2 import TranslationRequestMessage


class MosesServerWorker(AbstractWorkerServer):
    """
    Implementation of a worker server connecting to a Moses SMT server system.
    """
    __name__ = 'MosesServerWorker'
    MOSES_HOST = None
    MOSES_PORT = None
    MOSES_SOURCE = None
    MOSES_TARGET = None
    
    @staticmethod
    def usage():
        """
        Returns usage information, e.g. for additional parameters, etc.
        """
        return ('MOSES_HOST=http://example.org',
          'MOSES_PORT=port_number',
          'MOSES_SOURCE=source_language_iso639_2_code',
          'MOSES_TARGET=target_language_iso639_2_code')
    
    def parse_args(self, args):
        """
        Parses the given args list and sets worker specific paramters.
        """
        for arg in args:
            try:
                key, value = arg.split('=')
            
            except ValueError:
                continue
            
            if key == 'MOSES_HOST':
                print "Setting MOSES_HOST={0}".format(value)
                self.MOSES_HOST = value

            elif key == 'MOSES_PORT':
                print "Setting MOSES_PORT={0}".format(value)
                self.MOSES_PORT = value

            elif key == 'MOSES_SOURCE':
                print "Setting MOSES_SOURCE={0}".format(value)
                self.MOSES_SOURCE = value

            elif key == 'MOSES_TARGET':
                print "Setting MOSES_TARGET={0}".format(value)
                self.MOSES_TARGET = value
        
        if not self.MOSES_HOST or not self.MOSES_PORT or \
          not self.MOSES_SOURCE or not self.MOSES_TARGET:
            return False
        
        return True

    def language_pairs(self):
        """
        Returns a tuple of all supported language pairs for this worker.
        """
        return (
          (self.MOSES_SOURCE, self.MOSES_TARGET),
        )

    def language_code(self, iso639_2_code):
        """
        Converts a given ISO-639-2 code into the worker representation.

        Returns None for unknown languages.
        """
        return iso639_2_code

    def is_alive(self):
        """
        Checks if the Lucy RBMT XML-RPC interface is running.
        """
        proxy = xmlrpclib.ServerProxy('{0}:{1}'.format(self.MOSES_HOST,
          self.MOSES_PORT))
        try:
            _ = proxy.system.listMethods()
        
        except:
            return False
        
        return True

    def handle_translation(self, request_id):
        """
        Translates text using the connected Moses SMT server system.
        """
        handle = open('/tmp/{0}.message'.format(request_id), 'r+b')
        message = TranslationRequestMessage()
        message.ParseFromString(handle.read())

        proxy = xmlrpclib.ServerProxy('{0}:{1}'.format(self.MOSES_HOST,
          self.MOSES_PORT))

        result = []
        for text in message.source_text.split(u'\n'):
            content = proxy.translate({'text': text})
            result.append(content.get('text', '\n'))

        if result:
            message.target_text = u'\n'.join(result)

        handle.seek(0)
        handle.write(message.SerializeToString())
        handle.close()
