"""
Implementation of a worker server that connects to the Lucy RBMT system.
"""
import re
import sys
import xmlrpclib

from worker import AbstractWorkerServer


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
        source = open('/tmp/{0}.source'.format(request_id), 'r')
        text = source.read()
        source.close()
        
        proxy = xmlrpclib.ServerProxy('http://msv-3207.sb.dfki.de:9999/')
        assert(proxy.isAlive())
        
        content = proxy.lucyTranslate(text, 'GERMAN', 'ENGLISH')
        result = content.get('EN.txt')
        
        if result:
            target = open('/tmp/{0}.target'.format(request_id), 'w')
            target.write(result.group(1))
            target.close()


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print "\n\tusage {0} <host> <port>\n".format(sys.argv[0])
        sys.exit(-1)

    # Prepare XML-RPC server instance running on hostname:port.
    SERVER = LucyWorker(sys.argv[1], int(sys.argv[2]),
      '/tmp/workerserver-lucy.log')

    # Start server and serve forever.
    SERVER.start_worker()