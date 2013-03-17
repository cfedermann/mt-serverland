"""
Project: MT Server Land
 Author: Christian Federmann <cfedermann@dfki.de>
"""
import logging
from django.contrib.auth.views import login as LOGIN, logout as LOGOUT
from django.shortcuts import render_to_response
from django.template import RequestContext
from serverland.settings import LOG_LEVEL, LOG_HANDLER

# Setup logging support.
logging.basicConfig(level=LOG_LEVEL)
LOGGER = logging.getLogger('serverland.views')
LOGGER.addHandler(LOG_HANDLER)

def frontpage(request):
    """Renders the front page view."""
    LOGGER.info('Rendering frontpage view for user "{0}".'.format(
      request.user.username or "Anonymous"))
    
    dictionary = {'title': 'Welcome to MT Server Land',
      'active_page': 'home'}
    return render_to_response('frontpage.html', dictionary,
      context_instance=RequestContext(request))


def login(request):
    """Renders login view by connecting to django.contrib.auth.views."""
    LOGGER.info('Rendering login view for user "{0}".'.format(
      request.user.username or "Anonymous"))
    
    # TODO: add proper context dictionaries to login/logout views.
    #       Also, make sure to use proper "Sign in" and "Sign out" labels.
    
    return LOGIN(request)


def logout(request, next_page):
    """Renders logout view by connecting to django.contrib.auth.views."""
    LOGGER.info('Logging out user "{0}", redirecting to "{1}".'.format(
      request.user.username or "Anonymous", next_page)) 
    
    return LOGOUT(request, next_page)