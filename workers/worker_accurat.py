"""
Implementation of a worker server that connects ACCURAT Moses instances.
"""
import sys
from subprocess import Popen
from time import sleep

from workers.worker import AbstractWorkerServer
from protobuf.TranslationRequestMessage_pb2 import TranslationRequestMessage


class AccuratWorker(AbstractWorkerServer):
    """
    Implementation of a worker server that connects ACCURAT Moses instances.
    """
    __name__ = 'AccuratWorker'
    N_BEST = None

    @staticmethod
    def usage():
        """
        Returns usage information, e.g. for additional parameters, etc.
        """
        return ('N_BEST=max_number_of_parallel_jobs',)
    
    def parse_args(self, args):
        """
        Parses the given args list and sets worker specific paramters.
        """
        for arg in args:
            try:
                key, value = arg.split('=')
            
            except ValueError:
                continue
            
            if key == 'N_BEST':
                print "Setting N_BEST={0}".format(value)
                self.N_BEST = int(value)
        
        if not self.N_BEST:
            return False
        
        return True
    
    def language_pairs(self):
        """
        Returns a tuple of all supported language pairs for this worker.
        """
        return (('ger', 'eng'), ('gre', 'rum'), ('slv', 'eng'),
          ('rum', 'eng'), ('rum', 'gre'), ('rum', 'ger'), ('lav', 'lit'),
          ('lit', 'rum'), ('hrv', 'eng'), ('eng', 'slv'), ('eng', 'rum'),
          ('eng', 'lav'), ('eng', 'lit'), ('eng', 'hrv'), ('eng', 'est'),
          ('eng', 'gre'), ('ger', 'rum'))
    
    def language_code(self, iso639_2_code):
        """
        Converts a given ISO-639-2 code into the worker representation.

        Returns None for unknown languages.
        """
        mapping = {
          'ger': 'de', 'eng': 'en', 'gre': 'el', 'rum': 'ro', 'slv': 'sl',
          'lav': 'lv', 'lit': 'lt', 'hrv': 'hr', 'est': 'et'
        }
        return mapping.get(iso639_2_code)

    def is_busy(self):
        """
        Checks if the worker server is currently busy.
        """
        if sum([p.is_alive() for p in self.jobs.values()]) >= self.N_BEST:
            return True

        return False

    def start_translation(self, serialized):
        if self.is_busy():
            return False
        
        super(AccuratWorker, self).start_translation(serialized)
    
    def handle_translation(self, request_id):
        """
        Translates text using the Accurat Moses SMT system.
        """
        handle = open('/tmp/{0}.message'.format(request_id), 'r+b')
        message = TranslationRequestMessage()
        message.ParseFromString(handle.read())

        # First, we write out the source text to file.
        source = open('/tmp/{0}.source'.format(request_id), 'w')
        source.write(message.source_text.encode('utf-8'))
        
        # Check if the last line ends with a line break, otherwise Moses
        # I/O implementation does not accept the input!
        if not message.source_text.endswith('\n'):
            source.write('\n')
        source.close()
        
        source_language = self.language_code(message.source_language)
        target_language = self.language_code(message.target_language)
        
        # This is a special instance of the Moses worker, with pre-defined
        # knowledge about the ACCURAT Moses configurations.  We use this
        # approach to ensure that only one Moses process at a time can be
        # started; by doing so, we can avoid memory issues.
        MOSES_CMD = '/share/accurat/run/wmt10/bin/moses-irstlm/mosesdecoder' \
          '/mosesdecoder/moses-cmd/src/moses'
        
        MOSES_CONFIG = '/share/accurat/mtserver/accurat/{0}-{1}/' \
          'moses.ini.bin'.format(source_language, target_language)
        
        # Then, we invoke the Moses command reading from the source file
        # and writing to a target file, also inside /tmp.  This blocks until
        # the Moses process finishes.
        shell_cmd = "{0} -f {1} < /tmp/{2}.source > /tmp/{3}.target".format(
          MOSES_CMD, MOSES_CONFIG, request_id, request_id)
        process = Popen(shell_cmd, shell=True)
        process.wait()

        # Wait for some time to ensure file I/O is completed.
        sleep(2)

        # We can now load the translation from the target file.
        target = open('/tmp/{0}.target'.format(request_id), 'r')
        target_text = target.read()
        message.target_text = unicode(target_text, 'utf-8')
        target.close()

        handle.seek(0)
        handle.write(message.SerializeToString())
        handle.close()
