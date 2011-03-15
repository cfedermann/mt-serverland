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
    __splitter__ = '[[YAHOO_SPLITTER]]'
    __batch__ = 200

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

    def _batch_translate(self, source, target, text):
        """Translates a text using Microsoft Translator."""
        the_data = urllib.urlencode({'lp': '{0}_{1}'.format(source, target),
          'text': text.encode('utf-8'), 'ei': 'utf8'})
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
                    _current_line.append(target_line.decode('latin-1'))
                else:
                    _target_text.append(u' '.join(_current_line))
                    _current_line = []

            return u'\n'.join(_target_text)

        else:
            return "ERROR: result_exp did not match.\nCONTENT: {0}".format(
              content)

    def handle_translation(self, request_id):
        """
        Handler connecting to the Yahoo! Babel Fish service.
        """
        handle = open('/tmp/{0}.message'.format(request_id), 'r+b')
        message = TranslationRequestMessage()
        message.ParseFromString(handle.read())

        source = self.language_code(message.source_language)
        target = self.language_code(message.target_language)

        # Insert splitter tokens to allow re-construction of original lines.
        _source_text = []
        for source_line in message.source_text.split('\n'):
            _source_text.append(source_line.strip())
            _source_text.append(self.__splitter__)

        result = u''
        batches = len(_source_text) / self.__batch__
        for batch in range(batches):
            _start = batch * self.__batch__
            _end = _start + self.__batch__
            text = u'\n'.join(_source_text[_start:_end])
            result += self._batch_translate(source, target, text)
            result += '\n'
        
        last_batch = len(_source_text) % self.__batch__
        if last_batch:
            print last_batch
            text = u'\n'.join(_source_text[-last_batch:])
            print text
            result += self._batch_translate(source, target, text)
            result += '\n'

        message.target_text = result
        handle.seek(0)
        handle.write(message.SerializeToString())
        handle.close()
