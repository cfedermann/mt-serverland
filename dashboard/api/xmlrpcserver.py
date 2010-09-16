#!/usr/bin/env python

'''
XML-RPC interface to the serverland dashboard API.
Project: MT Server Land prototype code
Author: Will Roberts <William.Roberts@dfki.de>

Syntax:
   python xmlrpcserver.py hostname portnum dashboard_api_url

hostname          -- the address to bind to
portnum           -- the port number to bind to
dashboard_api_url -- the URL of the serverland dashboard API

'''

from SimpleXMLRPCServer import SimpleXMLRPCServer

# Question for Will: do we really need httplib2?
# - http://code.google.com/p/httplib2/
#
# Or would the httplib import suffice?
import httplib2

import json
import mimetools
import sys
import urlparse

CRLF = '\r\n'

def normalize_api_url (url):
    '''Normalizes the given URL to make sure it is pointing at a
    dashboard API instance.'''
    if not urlparse.urlparse(url).scheme:
        # default to HTTP if no protocol is specified
        url = 'http://' + url
    parsed_url = urlparse.urlparse(url)
    url_path = parsed_url.path
    if not url_path.endswith('/'):
        url_path += '/'
    url_path_parts = [ x for x in url_path.split('/') if x ]
    if url_path_parts[-2:] == ['dashboard', 'api']:
        pass
    elif url_path_parts[-1:] == ['dashboard']:
        url_path += 'api/'
    else:
        url_path += 'dashboard/api/'
    parsed_url = list(parsed_url)
    parsed_url[2] = url_path
    url = urlparse.urlunparse(parsed_url)
    return url


class XmlRpcAPIServer(object):
    '''
    An server that provides an XML-RPC interface to the dashboard API.
    '''

    finished = False
    server = None
    api_url = None

    def __init__(self, host, port, api_url):
        '''
        Creates a new XmlRpcAPIServer instance serving from host:port.
        '''
        self.http = httplib2.Http()
        self.server = SimpleXMLRPCServer((host, port), allow_none=True)
        self.server.register_function(self.stop_server)
        self.server.register_function(self.list_workers)
        self.server.register_function(self.list_requests)
        self.server.register_function(self.create_translation)
        self.server.register_function(self.delete_translation)
        self.server.register_function(self.list_results)
        self.api_url = normalize_api_url(api_url)

    def start_server(self):
        '''
        Starts the event handler of the XML-RPC API interface server.
        '''
        print 'Starting server'
        print 'Dashboard API lives at {0}'.format(self.api_url)
        while not self.finished:
            self.server.handle_request()

    def stop_server(self):
        '''
        Stops the event handler of the XML-RPC API interface server.
        '''
        if not self.finished:
            self.finished = True

    def list_workers(self, token, shortname = None):
        '''
        Queries the server for workers.
        '''
        if shortname is not None:
            url = self.api_url + 'workers/{0}/?token={1}'.format(shortname,
              token)
        else:
            url = self.api_url + 'workers/?token={0}'.format(token)
        response = self.http.request(url, method='GET')
        if response[0].status == 200:
            return json.loads(response[1])
        else:
            raise Exception(response[0].reason)

    def list_requests(self, token, shortname_or_request_id = None):
        '''
        Queries the server for translation requests.
        '''
        if shortname_or_request_id is not None:
            url = self.api_url + 'requests/{0}/?token={1}'.format(
              shortname_or_request_id, token)
        else:
            url = self.api_url + 'requests/?token={0}'.format(token)
        response = self.http.request(url, method='GET')
        if response[0].status == 200:
            return json.loads(response[1])
        else:
            raise Exception(response[0].reason)

    def create_translation(self, token, request_shortname, worker_shortname,
                           source_language, target_language, file_name,
                           file_contents):
        '''
        Submits a new translation request.

        multipart/form-data
        '''
        contents = {}
        contents['token'] = token
        contents['shortname'] = request_shortname
        contents['worker'] = worker_shortname
        contents['source_language'] = source_language
        contents['target_language'] = target_language
        file_lines = file_contents.split('\n')
        boundary = '-----' + mimetools.choose_boundary() + '-----'
        body = []
        for (key, value) in contents.items():
            body.append('--' + boundary)
            body.append('Content-Disposition: form-data; name="{0}"'.format(
              key))
            body.append('')
            body.append(value)
        body.append('--' + boundary)
        body.append('Content-Disposition: form-data; ' +
                      'name="source_text"; ' +
                      'filename="{0}"'.format(file_name))
        body.append('Content-Type: text/plain')
        body.append('')
        body.extend(file_lines)
        body.append('--' + boundary)
        body.append('')
        body = CRLF.join(body)
        content_type = 'multipart/form-data; boundary={0}'.format(boundary)
        header = {'Content-type': content_type,
                  'Content-length': str(len(body))}
        response = self.http.request(self.api_url + 'requests/',
                                     method='POST', body=body, headers=header)
        if response[0].status == 201:
            return json.loads(response[1])
        else:
            raise Exception(response[0].reason)

    def delete_translation(self, token, shortname_or_request_id):
        '''
        Deletes a translation request.
        '''
        url = self.api_url + 'requests/{0}/?token={1}'.format(
            shortname_or_request_id, token)
        response = self.http.request(url, method='DELETE')
        if response[0].status == 204:
            return True
        else:
            raise Exception(response[0].reason)

    def list_results(self, token, shortname_or_request_id = None):
        '''
        Queries the server for translation results.
        '''
        if shortname_or_request_id is not None:
            url = self.api_url + 'results/{0}/?token={1}'.format(
                shortname_or_request_id, token)
        else:
            url = self.api_url + 'results/?token={0}'.format(token)
        response = self.http.request(url, method='GET')
        if response[0].status == 200:
            return json.loads(response[1])
        else:
            raise Exception(response[0].reason)


def main():
    '''Main function.'''
    if len(sys.argv) < 4:
        print __doc__.strip()
        print
        sys.exit(0)
    server = XmlRpcAPIServer(sys.argv[1], int(sys.argv[2]), sys.argv[3])
    server.start_server()

if __name__ == '__main__' and sys.argv != ['']:
    main()
