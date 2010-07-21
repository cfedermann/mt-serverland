#!/usr/bin/python
"""
Startup script to create a worker server instance at host:port.
"""
import sys

from worker import DummyWorker

# Make configurable:
#
# - working folder where files are stored
# - logfile location
#
# Fix AssertionError ;)

REGISTERED_WORKERS = {
  'DummyWorker': (DummyWorker, '/tmp/workerserver-dummy.log'),
}

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print "\n\tusage: {0} <worker> <host> <port>\n".format(sys.argv[0])
        
        if len(REGISTERED_WORKERS):
            print "\tregistered worker servers:"
            print "\t- {0}\n".format("\n\t- ".join(REGISTERED_WORKERS.keys()))
        
        sys.exit(-1)
    
    assert(sys.argv[1] in REGISTERED_WORKERS.keys())

    # Prepare XML-RPC server instance running on host:port.
    WORKER_IMPLEMENTATION, LOGFILE = REGISTERED_WORKERS[sys.argv[1]]
    SERVER = WORKER_IMPLEMENTATION(sys.argv[2], int(sys.argv[3]), LOGFILE)

    # Start server and serve forever.
    SERVER.start_worker()