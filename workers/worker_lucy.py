"""
Implementation of a worker server that connects to the Lucy RBMT system.
"""
import sys
import xmlrpclib

from worker import AbstractWorkerServer
from TranslationRequestMessage_pb2 import TranslationRequestMessage


class LucyWorker(AbstractWorkerServer):
    """
    Implementation of a worker server that connects to the Lucy RBMT system.
    """
    __name__ = 'LucyWorker'
    
    def handle_translation(self, request_id):
        """
        Translates text from German->English using the Lucy RBMT system.

        Uses the XML-RPC server wrapper running at msv-3207.sb.dfki.de.
        """
        handle = open('/tmp/{0}.message'.format(request_id), 'r+b')
        message = TranslationRequestMessage()
        message.ParseFromString(handle.read())
        
        proxy = xmlrpclib.ServerProxy('http://msv-3207.sb.dfki.de:9999/')
        assert(proxy.isAlive())
        
        content = proxy.lucyTranslate(message.source_text, 'GERMAN',
          'ENGLISH')
        result = content.get('EN.txt')

        # We have to parse the result text and filter out Lucy's alternative
        # translations, e.g.:
        #
        # The apple does not fall far from the <A[tribe|stem|trunk]>.
        if result:
            message.target_text = result
            handle.seek(0)
            handle.write(message.SerializeToString())

        handle.close()


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print "\n\tusage {0} <host> <port>\n".format(sys.argv[0])
        sys.exit(-1)

    # Prepare XML-RPC server instance running on hostname:port.
    SERVER = LucyWorker(sys.argv[1], int(sys.argv[2]),
      '/tmp/workerserver-lucy.log')

    # Start server and serve forever.
    SERVER.start_worker()