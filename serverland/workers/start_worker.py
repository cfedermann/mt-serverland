#!/usr/bin/python
"""
Startup script to create a worker server instance at host:port.
"""
import sys

from workers.worker import DummyWorker
from workers.worker_bing import BingWorker
from workers.worker_google import GoogleWorker
from workers.worker_lucy import LucyWorker
from workers.worker_yahoo import YahooWorker
from workers.worker_moses import MosesWorker
from workers.worker_moses_server import MosesServerWorker
from workers.worker_accurat import AccuratWorker

# Make configurable:
#
# - working folder where files are stored

REGISTERED_WORKERS = {
  'DummyWorker': (DummyWorker, '/tmp/workerserver-dummy.log'),
  'BingWorker': (BingWorker, '/tmp/workerserver-bing.log'),
  'GoogleWorker': (GoogleWorker, '/tmp/workerserver-google.log'),
  'LucyWorker': (LucyWorker, '/tmp/workerserver-lucy.log'),
  'YahooWorker': (YahooWorker, '/tmp/workerserver-yahoo.log'),
  'MosesWorker': (MosesWorker, '/tmp/workerserver-moses.log'),
  'MosesServerWorker': (MosesServerWorker,
    '/tmp/workerserver-mosesserver.log'),
  'AccuratWorker': (AccuratWorker, '/tmp/workerserver-accurat.log')
}


if __name__ == "__main__":
    if len(sys.argv) < 4 or not sys.argv[1] in REGISTERED_WORKERS.keys():
        print "\n\tusage: {0} <worker> <host> <port> " \
          "[LOGFILE=/path/to/logfile]\n".format(sys.argv[0])

        if len(REGISTERED_WORKERS):
            print "\tregistered worker servers:"
            for key, value in REGISTERED_WORKERS.items():
                print "\t- {0}".format(key)
                usage = value[0].usage()
                
                if len(usage):
                    for line in usage:
                        print "\t  > {0}".format(line)
                    print
            print

        sys.exit(-1)

    # Prepare XML-RPC server instance running on host:port.
    LOGFILE = None
    kwargs = sys.argv[4:]
    for arg in kwargs:
        if arg.startswith('LOGFILE='):
            LOGFILE = arg.split('=')[1]
    
    if LOGFILE:
        WORKER_IMPLEMENTATION, _ = REGISTERED_WORKERS[sys.argv[1]]
    else:
        WORKER_IMPLEMENTATION, LOGFILE = REGISTERED_WORKERS[sys.argv[1]]
    
    SERVER = WORKER_IMPLEMENTATION(sys.argv[2], int(sys.argv[3]), LOGFILE)

    # Parse additional parameters.
    ready = SERVER.parse_args(kwargs)
    if not ready:
        print "\n\tusage: {0} <worker> <host> <port> " \
          "LOGFILE=/path/to/logfile\n".format(sys.argv[0])
        print "\t- {0}".format(sys.argv[1])
        usage = WORKER_IMPLEMENTATION.usage()
        
        if len(usage):
            for line in usage:
                print "\t  > {0}".format(line)
            print ""
        
        sys.exit(-1)

    # Start server and serve forever.
    SERVER.start_worker()