"""
Implementation of a worker server that connects to Google Translate.
"""
import re
import sys
import urllib
import urllib2

from worker import AbstractWorkerServer
from TranslationRequestMessage_pb2 import TranslationRequestMessage


class GoogleWorker(AbstractWorkerServer):
    """
    Implementation of a worker server that connects to Google Translate.
    """
    __name__ = 'GoogleWorker'

    def language_pairs(self):
        """
        Returns a tuple of all supported language pairs for this worker.
        """
        languages = ['eng', 'fre', 'ger', 'spa']
        return tuple([(a,b) for a in languages for b in languages if a != b])
    
    def language_code(self, iso639_2_code):
        """
        Converts a given ISO-639-2 code into the worker representation.
        
        Returns None for unknown languages.
        """
        mapping = {
          'eng': 'en', 'fre': 'fr', 'ger': 'de', 'spa': 'es'
        }
        return mapping.get(iso639_2_code)

    def handle_translation(self, request_id):
        """
        Translation handler that obtains a translation via the Google
        translation web front end.

        Currently hard-coded to the language pair DE -> EN.

        """
        handle = open('/tmp/{0}.message'.format(request_id), 'r+b')
        message = TranslationRequestMessage()
        message.ParseFromString(handle.read())
        
        source = self.language_code(message.source_language)
        target = self.language_code(message.target_language)
        
        the_url = 'http://translate.google.com/translate_t'
        the_data = urllib.urlencode({'js': 'n', 'text': message.source_text.encode('utf-8'),
          'sl': source, 'tl': target})
        the_header = {'User-agent': 'Mozilla/5.0'}

        opener = urllib2.build_opener(urllib2.HTTPHandler)        
        http_request = urllib2.Request(the_url, the_data, the_header)
        http_handle = opener.open(http_request)
        content = http_handle.read()
        http_handle.close()
        
        result_exp = re.compile('<textarea name=utrans wrap=SOFT ' \
          'dir="ltr" id=suggestion.*>(.*?)</textarea>', re.I|re.U)
        
        result = result_exp.search(content)
        
        if result:
            target_html = result.group(1)
            target_text = target_html.replace('&lt;br&gt;', '\n')
            message.target_text = unicode(target_text, 'utf-8')
            handle.seek(0)
            handle.write(message.SerializeToString())

        handle.close()


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print "\n\tusage {0} <host> <port>\n".format(sys.argv[0])
        sys.exit(-1)

    # Prepare XML-RPC server instance running on hostname:port.
    SERVER = GoogleWorker(sys.argv[1], int(sys.argv[2]),
      '/tmp/workerserver-google.log')

    # Start server and serve forever.
    SERVER.start_worker()