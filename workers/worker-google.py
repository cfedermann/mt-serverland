"""
Implementation of a worker server that connects to Google Translate.

Currently translates from German->English only.
"""
import logging
import re
import sys
import urllib
import urllib2
import xmlrpclib

from base64 import b64encode, b64decode
from multiprocessing import Process
from os import remove
from time import sleep
from random import random
from SimpleXMLRPCServer import SimpleXMLRPCServer

from worker import WorkerServer


class GoogleWorkerServer(WorkerServer):
    """
    Implementation of a worker server that connects to Google Translate.
    """
    __name__ = 'GoogleWorkerServer'
    
    def handle_translation(self, request_id):
        """
        Dummy translation handler that blocks for a random amount of time.

        Returns all-uppercase version of Text as translation.
        """
        source = open('/tmp/{0}.source'.format(request_id), 'r')
        text = source.read()
        source.close()
        
        opener = urllib2.build_opener(urllib2.HTTPHandler)
        
        the_url = 'http://translate.google.com/translate_t'
        the_data = urllib.urlencode({'js': 'n', 'text': text, 'sl': 'de',
          'tl': 'en'})
        the_header = {'User-agent': 'Mozilla/5.0'}
        
        request = urllib2.Request(the_url, the_data, the_header)
        handle = opener.open(request)
        content = handle.read()
        handle.close()
        #raw_result = unicode(content, 'utf-8')
        
        result_exp = re.compile('<textarea name=utrans wrap=SOFT dir="ltr" id=suggestion.*>(.*?)</textarea>',
          re.I|re.U)
        
        result = result_exp.search(content)
        
        if result:
            target = open('/tmp/{0}.target'.format(request_id), 'w')
            target.write(result.group(1))
            target.close()


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print "\n\tusage {0} <host> <port>\n".format(sys.argv[0])
        sys.exit(-1)

    # Prepare XML-RPC server instance running on localhost:6666.
    server = GoogleWorkerServer(sys.argv[1], int(sys.argv[2]),
      '/tmp/workerserver-google.log')

    # Start server and serve forever.
    server.start()