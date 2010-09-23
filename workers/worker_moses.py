"""
Implementation of a worker server that starts a Moses SMT system.
"""
import sys
from subprocess import Popen

from workers.worker import AbstractWorkerServer
from protobuf.TranslationRequestMessage_pb2 import TranslationRequestMessage


class MosesWorker(AbstractWorkerServer):
    """
    Implementation of a worker server that starts a Moses SMT system.
    """
    __name__ = 'MosesWorker'
    MOSES_CMD = None
    MOSES_CONFIG = None
    MOSES_SOURCE = None
    MOSES_TARGET = None
    
    @staticmethod
    def usage():
        """
        Returns usage information, e.g. for additional parameters, etc.
        """
        return ('MOSES_CMD=/path/to/moses/binary',
          'MOSES_CONFIG=/path/to/moses/config>',
          'MOSES_SOURCE=source_language_iso639_2_code',
          'MOSES_TARGET=target_language_iso639_2_code')
    
    def parse_args(self, args):
        """
        Parses the given args list and sets worker specific paramters.
        """
        for arg in args:
            try:
                key, value = arg.split('=')
            
            except ValueError:
                continue
            
            if key == 'MOSES_CMD':
                print "Setting MOSES_CMD={0}".format(value)
                self.MOSES_CMD = value

            elif key == 'MOSES_CONFIG':
                print "Setting MOSES_CONFIG={0}".format(value)
                self.MOSES_CONFIG = value

            elif key == 'MOSES_SOURCE':
                print "Setting MOSES_SOURCE={0}".format(value)
                self.MOSES_SOURCE = value

            elif key == 'MOSES_TARGET':
                print "Setting MOSES_TARGET={0}".format(value)
                self.MOSES_TARGET = value
        
        if not self.MOSES_CMD or not self.MOSES_CONFIG or \
          not self.MOSES_SOURCE or not self.MOSES_TARGET:
            return False
        
        return True

    def language_pairs(self):
        """
        Returns a tuple of all supported language pairs for this worker.
        """
        return (
          (MOSES_SOURCE, MOSES_TARGET),
        )

    def language_code(self, iso639_2_code):
        """
        Converts a given ISO-639-2 code into the worker representation.

        Returns None for unknown languages.
        """
        return iso639_2_code

    def handle_translation(self, request_id):
        """
        Translates text from German->English using the Moses SMT system.

        You have to adapt MOSES_CMD and MOSES_CONFIG to the correct values :)
        """
        handle = open('/tmp/{0}.message'.format(request_id), 'r+b')
        message = TranslationRequestMessage()
        message.ParseFromString(handle.read())

        # First, we write out the source text to file.
        source = open('/tmp/{0}.source'.format(request_id), 'w')
        source.write(message.source_text.encode('utf-8'))
        source.close()

        # Then, we invoke the Moses command reading from the source file
        # and writing to a target file, also inside /tmp.  This blocks until
        # the Moses process finishes.
        shell_cmd = "{0} -f {1} < /tmp/{2}.source > /tmp/{3}.target".format(
          MOSES_CMD, MOSES_CONFIG, request_id, request_id)
        process = Popen(shell_cmd, shell=True)
        process.wait()

        # We can now load the translation from the target file.
        target = open('/tmp/{0}.target'.format(request_id), 'r')
        message.target_text = unicode(target.read(), 'utf-8')
        target.close()

        handle.seek(0)
        handle.write(message.SerializeToString())
        handle.close()


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print "\n\tusage {0} <host> <port>\n".format(sys.argv[0])
        sys.exit(-1)

    # Prepare XML-RPC server instance running on hostname:port.
    SERVER = MosesWorker(sys.argv[1], int(sys.argv[2]),
      '/tmp/workerserver-moses.log')

    # Start server and serve forever.
    SERVER.start_worker()