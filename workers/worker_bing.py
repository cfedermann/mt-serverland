"""
Implementation of a worker server that connects to Microsoft Translator.
"""
import re
import sys
import urllib
import urllib2

from worker import AbstractWorkerServer
from TranslationRequestMessage_pb2 import TranslationRequestMessage


class BingWorker(AbstractWorkerServer):
    """
    Implementation of a worker server that connects to Microsoft Translator.
    """
    __name__ = 'BingWorker'
    
    def handle_translation(self, request_id):
        """
        Translates text from German->English using Microsoft Translator.

        Requires a Bing AppID as documented at MSDN:
        - http://msdn.microsoft.com/en-us/library/ff512421.aspx
        """
        message = open('/tmp/{0}.message'.format(request_id), 'r+b')
        request = TranslationRequestMessage()
        request.ParseFromString(message.read())
        
        opener = urllib2.build_opener(urllib2.HTTPHandler)
        
        app_id = '9259D297CB9F67680C259FD62734B07C0D528312'
        the_data = urllib.urlencode({'appId': app_id,
          'text': request.source_text, 'from': 'de', 'to': 'en'})
        the_url = 'http://api.microsofttranslator.com/v2/Http.svc/' \
          'Translate?{0}'.format(the_data)
        the_header = {'User-agent': 'Mozilla/5.0'}
        
        http_request = urllib2.Request(the_url, None, the_header)
        handle = opener.open(http_request)
        content = handle.read()
        handle.close()
        
        result_exp = re.compile('<string xmlns="http://schemas.microsoft.' \
          'com/2003/10/Serialization/">(.*?)</string>', re.I|re.U)
        
        result = result_exp.search(content)
        
        if result:
            request.target_text = result.group(1)
            message.seek(0)
            message.write(request.SerializeToString())

        message.close()


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print "\n\tusage {0} <host> <port>\n".format(sys.argv[0])
        sys.exit(-1)

    # Prepare XML-RPC server instance running on hostname:port.
    SERVER = BingWorker(sys.argv[1], int(sys.argv[2]),
      '/tmp/workerserver-bing.log')

    # Start server and serve forever.
    SERVER.start_worker()