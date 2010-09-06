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

# Make configurable:
#
# - working folder where files are stored
# - logfile location


REGISTERED_WORKERS = {
  'DummyWorker': (DummyWorker, '/tmp/workerserver-dummy.log'),
  'BingWorker': (BingWorker, '/tmp/workerserver-bing.log'),
  'GoogleWorker': (GoogleWorker, '/tmp/workerserver-google.log'),
  'LucyWorker': (LucyWorker, '/tmp/workerserver-lucy.log'),
  'YahooWorker': (YahooWorker, '/tmp/workerserver-yahoo.log')
}


if __name__ == "__main__":
    if len(sys.argv) != 4 or not sys.argv[1] in REGISTERED_WORKERS.keys():
        print "\n\tusage: {0} <worker> <host> <port>\n".format(sys.argv[0])

        if len(REGISTERED_WORKERS):
            print "\tregistered worker servers:"
            print "\t- {0}\n".format("\n\t- ".join(REGISTERED_WORKERS.keys()))

        sys.exit(-1)

    # Prepare XML-RPC server instance running on host:port.
    WORKER_IMPLEMENTATION, LOGFILE = REGISTERED_WORKERS[sys.argv[1]]
    SERVER = WORKER_IMPLEMENTATION(sys.argv[2], int(sys.argv[3]), LOGFILE)

    # Start server and serve forever.
    SERVER.start_worker()