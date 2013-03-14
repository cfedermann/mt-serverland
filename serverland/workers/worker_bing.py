"""
Implementation of a worker server that connects to Microsoft Translator.
"""
import re
import urllib2

from workers.worker import AbstractWorkerServer
from protobuf.TranslationRequestMessage_pb2 import TranslationRequestMessage


class BingWorker(AbstractWorkerServer):
    """
    Implementation of a worker server that connects to Microsoft Translator.
    
    MSDN reference information is available here:
    - http://msdn.microsoft.com/en-us/library/dd576287.aspx
    
    Microsoft Translator allows free translation of 2M characters/month.
    - https://datamarket.azure.com/dataset/1899a118-d202-492c-aa16-ba21c33c06cb
    
    """
    __name__ = 'BingWorker'
    __batch__ = 100

    # TODO: update language pairs to all 39 base languages.
    def language_pairs(self):
        """
        Returns a tuple of all supported language pairs for this worker.
        """
        languages = ('ara', 'bul', 'zho', 'ces', 'dan', 'nld', 'eng', 'est',
          'fin', 'fra', 'deu', 'ell', 'hat', 'heb', 'hun', 'ita', 'jpn',
          'kor', 'lav', 'lit', 'nor', 'pol', 'por', 'ron', 'rus', 'slk',
          'slv', 'spa', 'swe', 'tha', 'tur')
        return tuple([(a, b) for a in languages for b in languages if a != b])

    # MSDN gives a list of available language codes:
    # - http://msdn.microsoft.com/en-us/library/hh456380.aspx
    def language_code(self, iso639_3_code):
        """
        Converts a given ISO-639-3 code into the worker representation.

        Returns None for unknown languages.
        """
        mapping = {
          'ara': 'ar', 'bul': 'bg', 'zho': 'zh-CHS', 'ces': 'cs', 'dan': 'da',
          'nld': 'nl', 'eng': 'en', 'est': 'et', 'fin': 'fi', 'fra': 'fr',
          'deu': 'de', 'ell': 'el', 'hat': 'ht', 'heb': 'he', 'hun': 'hu',
          'ita': 'it', 'jpn': 'ja', 'kor': 'ko', 'lav': 'lv', 'lit': 'lt',
          'nor': 'no', 'pol': 'pl', 'por': 'pt', 'ron': 'ro', 'rus': 'ru',
          'slk': 'sk', 'slv': 'sl', 'spa': 'es', 'swe': 'sv', 'tha': 'th',
          'tur': 'tr'
        }
        return mapping.get(iso639_3_code)

    def _batch_translate(self, source, target, text):
        """Translates a text using Microsoft Translator."""
        app_id = '9259D297CB9F67680C259FD62734B07C0D528312'

        _texts = []
        for source_line in text.split('\n'):
            source_line = source_line.strip()

            _texts.append(u'<string xmlns="http://schemas.microsoft.com/' \
              '2003/10/Serialization/Arrays">{0}</string>'.format(
              source_line.replace(u'&', u'&amp;')))
        _texts = u'\n'.join(_texts).encode('utf-8')

        the_xml = """<?xml version="1.0" encoding="utf-8"?>
<TranslateArrayRequest>
<AppId>{0}</AppId>
<From>{1}</From>
<Texts>
{2}
</Texts>
<To>{3}</To>
</TranslateArrayRequest>""".format(app_id, source, _texts, target)

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

        result = result_exp.finditer(content)

        if result:
            _target_text = [m.group(1).decode('utf-8') for m in result]
            return u'\n'.join(_target_text).replace(u'&', u'&amp;')

        else:
            return u"ERROR: result_exp did not match.\nCONTENT: {0}".format(
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

        _source_text = message.source_text.split('\n')

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
            text = u'\n'.join(_source_text[-last_batch:])
            result += self._batch_translate(source, target, text)
            result += '\n'

        message.target_text = result
        handle.seek(0)
        handle.write(message.SerializeToString())
        handle.close()
