"""
Implementation of a worker server that connects to Yahoo! Babel Fish.
"""
import re
import sys
import urllib
import urllib2

from worker import AbstractWorkerServer


class YahooWorker(AbstractWorkerServer):
    """
    Implementation of a worker server that connects to Yahoo! Babel Fish.
    """
    __name__ = 'YahooWorker'
    
    def handle_translation(self, request_id):
        """
        Translates text from German->English using Yahoo! Babel Fish.
        """
        source = open('/tmp/{0}.source'.format(request_id), 'r')
        text = source.read()
        source.close()
        
        opener = urllib2.build_opener(urllib2.HTTPHandler)
        
        the_data = urllib.urlencode({'text': text, 'lp': 'de_en'})
        the_url = 'http://babelfish.yahoo.com/translate_txt?{0}'.format(
          the_data)
        the_header = {'User-agent': 'Mozilla/5.0'}
        
        request = urllib2.Request(the_url, None, the_header)
        handle = opener.open(request)
        content = handle.read()
        handle.close()
        
        result_exp = re.compile('<div id="result"><.*?>(.*?)</div></div>',
          re.I|re.U)
        
        result = result_exp.search(content)
        
        if result:
            target = open('/tmp/{0}.target'.format(request_id), 'w')
            target.write(result.group(1))
            target.close()


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print "\n\tusage {0} <host> <port>\n".format(sys.argv[0])
        sys.exit(-1)

    # Prepare XML-RPC server instance running on localhost:6666.
    SERVER = YahooWorker(sys.argv[1], int(sys.argv[2]),
      '/tmp/workerserver-google.log')

    # Start server and serve forever.
    SERVER.start_worker()