"""
Implementation of a worker server that connects to Yahoo! Babel Fish.
"""
import re
import sys
import urllib
import urllib2

from workers.worker import AbstractWorkerServer
from protobuf.TranslationRequestMessage_pb2 import TranslationRequestMessage


class YahooWorker(AbstractWorkerServer):
    """
    Implementation of a worker server that connects to Yahoo! Babel Fish.
    """
    __name__ = 'YahooWorker'

    def language_pairs(self):
        """
        Returns a tuple of all supported language pairs for this worker.
        """
        return (
          ('chi', 'eng'), ('eng', 'chi'), ('eng', 'dut'), ('eng', 'fre'),
          ('eng', 'ger'), ('eng', 'gre'), ('eng', 'ita'), ('eng', 'jpn'),
          ('eng', 'kor'), ('eng', 'por'), ('eng', 'rus'), ('eng', 'spa'),
          ('dut', 'eng'), ('dut', 'fre'), ('fre', 'dut'), ('fre', 'eng'),
          ('fre', 'ger'), ('fre', 'gre'), ('fre', 'ita'), ('fre', 'por'),
          ('fre', 'spa'), ('ger', 'eng'), ('ger', 'fre'), ('gre', 'eng'),
          ('gre', 'fre'), ('ita', 'eng'), ('ita', 'fre'), ('jpn', 'eng'),
          ('kor', 'eng'), ('por', 'eng'), ('por', 'fre'), ('rus', 'eng'),
          ('spa', 'eng'), ('spa', 'fre')
        )

    def language_code(self, iso639_2_code):
        """
        Converts a given ISO-639-2 code into the worker representation.

        Returns None for unknown languages.
        """
        mapping = {
          'chi': 'zh', 'dut': 'nl', 'eng': 'en', 'fre': 'fr', 'ger': 'de',
          'gre': 'el', 'ita': 'it', 'jpn': 'ja', 'kor': 'ko', 'por': 'pt',
          'rus': 'ru', 'spa': 'es'
        }
        return mapping.get(iso639_2_code)

    def handle_translation(self, request_id):
        """
        Translates text using Yahoo! Babel Fish.
        """
        handle = open('/tmp/{0}.message'.format(request_id), 'r+b')
        message = TranslationRequestMessage()
        message.ParseFromString(handle.read())

        source = self.language_code(message.source_language)
        target = self.language_code(message.target_language)

        the_data = urllib.urlencode({'lp': '{0}_{1}'.format(source, target),
          'text': message.source_text.encode('utf-8'), 'ei': 'utf8'})
        the_url = 'http://babelfish.yahoo.com/translate_txt?{0}'.format(
          the_data)
        the_header = {'User-agent': 'Mozilla/5.0'}

        opener = urllib2.build_opener(urllib2.HTTPHandler)
        http_request = urllib2.Request(the_url, None, the_header)
        http_handle = opener.open(http_request)
        content = http_handle.read()
        http_handle.close()

        result_exp = re.compile('type="hidden" name="p" value="([^"]+)',
          re.I|re.U)

        result = result_exp.search(content)

        if result:
            target_text = result.group(1)
            message.target_text = unicode(target_text, 'latin-1')
            handle.seek(0)
            handle.write(message.SerializeToString())

        handle.close()


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print "\n\tusage {0} <host> <port>\n".format(sys.argv[0])
        sys.exit(-1)

    # Prepare XML-RPC server instance running on hostname:port.
    SERVER = YahooWorker(sys.argv[1], int(sys.argv[2]),
      '/tmp/workerserver-yahoo.log')

    # Start server and serve forever.
    SERVER.start_worker()