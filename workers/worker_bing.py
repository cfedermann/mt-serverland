"""
Implementation of a worker server that connects to Microsoft Translator.
"""
import re
import sys
import urllib
import urllib2

from workers.worker import AbstractWorkerServer
from protobuf.TranslationRequestMessage_pb2 import TranslationRequestMessage


class BingWorker(AbstractWorkerServer):
    """
    Implementation of a worker server that connects to Microsoft Translator.
    """
    __name__ = 'BingWorker'
    __splitter__ = '[BING_SPLITTER_TOKEN]'
    __batch__ = 200

    def language_pairs(self):
        """
        Returns a tuple of all supported language pairs for this worker.
        """
        languages = ('ara', 'bul', 'chi', 'cze', 'dan', 'dut', 'eng', 'est',
          'fin', 'fre', 'ger', 'gre', 'hat', 'heb', 'hun', 'ita', 'jpn',
          'kor', 'lav', 'lit', 'nor', 'pol', 'por', 'rum', 'rus', 'slo',
          'slv', 'spa', 'swe', 'tha', 'tur')
        return tuple([(a,b) for a in languages for b in languages if a != b])

    def language_code(self, iso639_2_code):
        """
        Converts a given ISO-639-2 code into the worker representation.

        Returns None for unknown languages.
        """
        mapping = {
          'ara': 'ar', 'bul': 'bg', 'chi': 'zh-CHS', 'cze': 'cs', 'dan': 'da',
          'dut': 'nl', 'eng': 'en', 'est': 'et', 'fin': 'fi', 'fre': 'fr',
          'ger': 'de', 'gre': 'el', 'hat': 'ht', 'heb': 'he', 'hun': 'hu',
          'ita': 'it', 'jpn': 'ja', 'kor': 'ko', 'lav': 'lv', 'lit': 'lt',
          'nor': 'no', 'pol': 'pl', 'por': 'pt', 'rum': 'ro', 'rus': 'ru',
          'slo': 'sk', 'slv': 'sl', 'spa': 'es', 'swe': 'sv', 'tha': 'th',
          'tur': 'tr'
        }
        return mapping.get(iso639_2_code)


    def _batch_translate(self, source, target, text):
        """Translates a text using Microsoft Translator."""
        _text = unicode(text).encode('utf-8')
        app_id = '9259D297CB9F67680C259FD62734B07C0D528312'        
        the_xml = """<?xml version="1.0" encoding="utf-8"?>
<TranslateArrayRequest>
<AppId>{0}</AppId>
<From>{1}</From>
<Texts>
<string xmlns="http://schemas.microsoft.com/2003/10/Serialization/Arrays">{2}</string>
</Texts>
<To>{3}</To>
</TranslateArrayRequest>""".format(app_id, source, _text, target)
        the_url = 'http://api.microsofttranslator.com/v2/Http.svc/' \
          'TranslateArray'
        the_header = {'User-agent': 'Mozilla/5.0', 'Content-Type': 'text/xml'}

        opener = urllib2.build_opener(urllib2.HTTPHandler)
        http_request = urllib2.Request(the_url, the_xml, the_header)
        http_handle = opener.open(http_request)
        content = http_handle.read()
        http_handle.close()

        result_exp = re.compile('<TranslatedText>(.*?)</TranslatedText>',
          re.I|re.U|re.S)

        result = result_exp.search(content)

        if result:
            target_text = result.group(1)

            # Re-construct original lines using the splitter tokens.
            _target_text = []
            _current_line = []
            for target_line in target_text.split('\n'):
                target_line = target_line.strip()
                if target_line.strip('[]') != self.__splitter__.strip('[]'):
                    _current_line.append(unicode(target_line, 'utf-8'))
                else:
                    _target_text.append(u' '.join(_current_line))
                    _current_line = []

            return u'\n'.join(_target_text)

        else:
            return "ERROR: result_exp did not match.\nCONTENT: {0}".format(
              content)


    def handle_translation(self, request_id):
        """"
        Handler connecting to the Microsoft Translator service.

        Requires a Bing AppID as documented at MSDN:
        - http://msdn.microsoft.com/en-us/library/ff512421.aspx
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
            text = unicode(u'\n'.join(_source_text[_start:_end]))
            result += self._batch_translate(source, target, text)
            result += '\n'
        
        last_batch = len(_source_text) % self.__batch__
        if last_batch:
            print last_batch
            text = unicode(u'\n'.join(_source_text[-last_batch:]))
            print text
            result += self._batch_translate(source, target, text)
            result += '\n'

        message.target_text = result
        handle.seek(0)
        handle.write(message.SerializeToString())
        handle.close()
