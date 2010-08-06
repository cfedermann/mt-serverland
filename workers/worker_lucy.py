"""
Implementation of a worker server that connects to the Lucy RBMT system.
"""
import re
import sys
import xmlrpclib

from worker import AbstractWorkerServer
from TranslationRequestMessage_pb2 import TranslationRequestMessage


class LucyWorker(AbstractWorkerServer):
    """
    Implementation of a worker server that connects to the Lucy RBMT system.
    """
    __name__ = 'LucyWorker'

    def is_alive(self):
        """
        Checks if the Lucy RBMT XML-RPC interface is running.
        """
        proxy = xmlrpclib.ServerProxy('http://msv-3207.sb.dfki.de:9999/')
        return proxy.isAlive()

    def language_pairs(self):
        """
        Returns a tuple of all supported language pairs for this worker.
        """
        languages = ('eng', 'fre', 'ger', 'spa')
        return tuple([(a,b) for a in languages for b in languages if a != b])

    def language_code(self, iso639_2_code):
        """
        Converts a given ISO-639-2 code into the worker representation.

        Returns None for unknown languages.
        """
        mapping = {
          'eng': 'ENGLISH', 'fre': 'FRENCH', 'ger': 'GERMAN', 'spa': 'SPANISH'
        }
        return mapping.get(iso639_2_code)

    def handle_translation(self, request_id):
        """
        Translates text from German->English using the Lucy RBMT system.

        Uses the XML-RPC server wrapper running at msv-3207.sb.dfki.de.
        """
        handle = open('/tmp/{0}.message'.format(request_id), 'r+b')
        message = TranslationRequestMessage()
        message.ParseFromString(handle.read())

        proxy = xmlrpclib.ServerProxy('http://msv-3207.sb.dfki.de:9999/')
        assert(proxy.isAlive())

        source = self.language_code(message.source_language)
        target = self.language_code(message.target_language)
        content = proxy.lucyTranslate(message.source_text, source, target)

        # Results are stored in a field with key: '{EN,ES,DE,FR}.txt'.
        target_key = target[:2]
        if target_key == 'SP':
            target_key = 'ES'

        result = content.get('{0}.txt'.format(target_key))
        trees = content.get('tre')

        # We have to parse the result text and filter out Lucy's alternative
        # translations, e.g.:
        #
        #   The apple does not fall far from the <A[tribe|stem|trunk]>.
        #
        # For this example, we will return "...from the tribe." as target text
        # while the "raw" translation as well as the trees are return inside
        # the TranslationRequestMessage's packet_data list.
        if result:
            filter_exp = re.compile('<.\[(.+?)\|.+?\]>')
            filtered_result = filter_exp.sub('\g<1>', result)
            message.target_text = unicode(filtered_result, 'utf-8')
            keyvalue = message.packet_data.add()
            keyvalue.key = 'RAW_RESULT'
            keyvalue.value = result

        if trees:
            keyvalue = message.packet_data.add()
            keyvalue.key = 'TREES'
            keyvalue.value = trees

        handle.seek(0)
        handle.write(message.SerializeToString())
        handle.close()


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print "\n\tusage {0} <host> <port>\n".format(sys.argv[0])
        sys.exit(-1)

    # Prepare XML-RPC server instance running on hostname:port.
    SERVER = LucyWorker(sys.argv[1], int(sys.argv[2]),
      '/tmp/workerserver-lucy.log')

    # Start server and serve forever.
    SERVER.start_worker()