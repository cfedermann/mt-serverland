"""
Implementation of a worker server that connects to Google Translate.
"""
import re
import sys
import urllib
import urllib2

from workers.worker import AbstractWorkerServer
from protobuf.TranslationRequestMessage_pb2 import TranslationRequestMessage


class GoogleWorker(AbstractWorkerServer):
    """
    Implementation of a worker server that connects to Google Translate.
    """
    __name__ = 'GoogleWorker'
    __splitter__ = '[[GOOGLE_SPLITTER]]'
    __batch__ = 200

    def language_pairs(self):
        """
        Returns a tuple of all supported language pairs for this worker.
        """
        languages = ('afr', 'sqi', 'ara', 'hye', 'aze', 'eus', 'bel', 'bul',
          'cat', 'zho', 'hrv', 'ces', 'dan', 'nld', 'eng', 'est', 'tgl',
          'fin', 'fra', 'glg', 'kat', 'deu', 'ell', 'hat', 'heb', 'hin',
          'hun', 'isl', 'ind', 'gle', 'ita', 'jpn', 'kor', 'lav', 'lit',
          'mkd', 'msa', 'mlt', 'nor', 'fas', 'pol', 'por', 'ron', 'rus',
          'srp', 'slk', 'slv', 'spa', 'swa', 'swe', 'tha', 'tur', 'ukr',
          'urd', 'vie', 'cym', 'yid')
        return tuple([(a,b) for a in languages for b in languages if a != b])

    def language_code(self, iso639_3_code):
        """
        Converts a given ISO-639-3 code into the worker representation.

        Returns None for unknown languages.
        """
        mapping = {
          'afr': 'af', 'sqi': 'sq', 'ara': 'ar', 'hye': 'hy', 'aze': 'az',
          'eus': 'eu', 'bel': 'be', 'bul': 'bg', 'cat': 'ca', 'zho': 'zh-CN',
          'hrv': 'hr', 'ces': 'cs', 'dan': 'da', 'nld': 'nl', 'eng': 'en',
          'est': 'et', 'tgl': 'tl', 'fin': 'fi', 'fra': 'fr', 'glg': 'gl',
          'kat': 'ka', 'deu': 'de', 'ell': 'el', 'hat': 'ht', 'heb': 'iw',
          'hin': 'hi', 'hun': 'hu', 'isl': 'is', 'ind': 'id', 'gle': 'ir',
          'ita': 'it', 'jpn': 'ja', 'kor': 'ko', 'lav': 'lv', 'lit': 'lt',
          'mkd': 'mk', 'msa': 'ms', 'mlt': 'mt', 'nor': 'no', 'das': 'fa',
          'pol': 'pl', 'por': 'pt', 'ron': 'ro', 'rus': 'ru', 'srp': 'sr',
          'slk': 'sk', 'slv': 'sl', 'spa': 'es', 'swa': 'sw', 'swe': 'sv',
          'tha': 'th', 'tur': 'tr', 'ukr': 'uk', 'urd': 'ur', 'vie': 'vi',
          'cym': 'cy', 'yid': 'yi'
        }
        return mapping.get(iso639_3_code)

    def _batch_translate(self, source, target, text):
        """Translates a text using Google Translate."""
        the_url = 'http://translate.google.com/translate_t'
        the_data = urllib.urlencode({'js': 'n', 'sl': source, 'tl': target,
          'text': text.encode('utf-8')})
        the_header = {'User-agent': 'Mozilla/5.0'}

        opener = urllib2.build_opener(urllib2.HTTPHandler)
        http_request = urllib2.Request(the_url, the_data, the_header)
        http_handle = opener.open(http_request)
        content = http_handle.read()
        http_handle.close()

        result_exp = re.compile('<span id=result_box.*?>(.*)</span></div>',
          re.I|re.U|re.S)

        result = result_exp.search(content)

        if result:
            # Normalize HTML line breaks to \n.
            result = result.group(1).replace('<br>', '\n')

            # Extract all <span>...</span> tags containing the translation.
            span_exp = re.compile('<span.*?>([^<]+?)</span>', re.I|re.U|re.S)
            span_iter = span_exp.finditer(result)
            spans = [match.group(1).decode('utf-8') for match in span_iter]

            # Construct target text from list of spans, normalizing \n+ to \n.
            target_text = u'\n'.join([span.strip() for span in spans])  
            multibreaks = re.compile('\n+', re.I|re.U|re.S)
            target_text = multibreaks.sub(u'\n', target_text)

            # Re-construct original lines using the splitter tokens.
            _target_text = []
            _current_line = []
            for target_line in target_text.split('\n'):
                target_line = target_line.strip()
                if target_line.strip('[]') != self.__splitter__.strip('[]'):
                    _current_line.append(target_line.strip())
                else:
                    _target_text.append(u' '.join(_current_line))
                    _current_line = []

            return u'\n'.join(_target_text)

        else:
            return u"ERROR: result_exp did not match.\nCONTENT: {0}".format(
              content)

    def handle_translation(self, request_id):
        """
        Handler connecting to the Google Translate service.
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
            _source_text.append(unicode(self.__splitter__))

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
