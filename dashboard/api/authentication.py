'''
Authentication by token for the serverland dashboard Web API.
Project: MT Server Land prototype code
 Author: Will Roberts <William.Roberts@dfki.de>

'''

from piston.utils import rc, translate_mime
from serverland.dashboard.api.models import AuthToken
from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist

class TokenAuthentication(object):
    '''
    Token-based authentication for dashboard API access.

    Authorized users will have a 4-byte hexadecimal access token; by
    passing this value with the key "token" to an API method, the user
    will be authenticated.

    '''

    def is_authenticated(self, request):
        '''Determines whether a given HTTP request is authenticated or
        not, and sets the requests user field if it is.'''
        token = None
        # get a token if this is a GET
        if request.GET and 'token' in request.GET:
            token = request.GET['token']
        # get a token if this is a POST
        if request.POST and 'token' in request.POST:
            token = request.POST['token']
        # translate mime-types in the request if this is a mime
        # message
        translate_mime(request)
        # check if there's a token in the mime data
        if ( hasattr(request, 'data') and
             request.data and
             'token' in request.data ):
            token = request.data['token']
        if token:
            try:
                token = AuthToken.objects.get(auth_token = token)
                if token.enabled:
                    request.user = token.user
                    return True
            except (ObjectDoesNotExist, MultipleObjectsReturned):
                pass
        return False

    def challenge(self):
        '''Gives the HTTPResponse returned when is_authenticated
        returns False.'''
        return rc.FORBIDDEN
