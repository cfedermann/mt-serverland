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
    __splitter__ = '[YAHOO_SPLITTER_TOKEN]'

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

        # Insert splitter tokens to allow re-construction of original lines.
        _source_text = []
        for source_line in message.source_text.split('\n'):
            _source_text.append(source_line.strip().encode('utf-8'))
            _source_text.append(self.__splitter__)

        the_data = urllib.urlencode({'lp': '{0}_{1}'.format(source, target),
          'text': u'\n'.join(_source_text), 'ei': 'utf8'})
        the_url = 'http://babelfish.yahoo.com/translate_txt'
        the_header = {'User-agent': 'Mozilla/5.0'}

        opener = urllib2.build_opener(urllib2.HTTPHandler)
        http_request = urllib2.Request(the_url, the_data, the_header)
        http_handle = opener.open(http_request)
        content = http_handle.read()
        http_handle.close()

        result_exp = re.compile(
          '<div id="result"><div.*?>([^<]+)</div></div>', re.I|re.U|re.S)

        result = result_exp.search(content)

        if result:
            target_text = result.group(1)

            # Re-construct original lines using the splitter tokens.
            _target_text = []
            _current_line = []
            for target_line in target_text.split('\n'):
                target_line = target_line.strip()
                if target_line.strip('[]') != self.__splitter__.strip('[]'):
                    _current_line.append(unicode(target_line, 'latin-1'))
                else:
                    _target_text.append(u' '.join(_current_line))
                    _current_line = []

            message.target_text = u'\n'.join(_target_text)
            handle.seek(0)
            handle.write(message.SerializeToString())

        else:
            message.target_text = "ERROR: result_exp did not match.\n" \
              "CONTENT: {0}".format(content)
            handle.seek(0)
            handle.write(message.SerializeToString())

        handle.close()
