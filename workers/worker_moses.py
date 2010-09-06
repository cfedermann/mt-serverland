"""
Implementation of a worker server that starts a Moses SMT system.
"""
import sys
from subprocess import Popen

from workers.worker import AbstractWorkerServer
from protobuf.TranslationRequestMessage_pb2 import TranslationRequestMessage


# Current settings just pass through the input, adapt to your Moses setup!
MOSES_CMD = "echo"
MOSES_CONFIG = ";cat"

class MosesWorker(AbstractWorkerServer):
    """
    Implementation of a worker server that starts a Moses SMT system.
    """
    __name__ = 'MosesWorker'

    def language_pairs(self):
        """
        Returns a tuple of all supported language pairs for this worker.
        """
        return (
          ('ger', 'eng'), # TODO: Make the output dependent on actual config.
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