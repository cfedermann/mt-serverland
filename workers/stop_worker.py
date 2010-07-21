#!/usr/bin/python
"""
Stop script to terminate a worker server instance serving from host:port.
"""
import sys
import xmlrpclib

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print "\n\tusage: {0} <host> <port>\n".format(sys.argv[0])
        sys.exit(-1)
    
    PROXY = xmlrpclib.ServerProxy('http://{0}:{1}/'.format(sys.argv[1],
      sys.argv[2]))
    PROXY.stop_worker()
