#!/usr/bin/python
import sys
import xmlrpclib

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print "\n\tusage: {0} <host> <port>\n".format(sys.argv[0])
        sys.exit(-1)
    
    proxy = xmlrpclib.ServerProxy('http://{0}:{1}/'.format(sys.argv[1],
      sys.argv[2]))
    proxy.stop_worker()
