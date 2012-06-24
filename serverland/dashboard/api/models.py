"""
Database model for authentication tokens used for the serverland
dashboard Web API.
Project: MT Server Land prototype code
 Author: Will Roberts <William.Roberts@dfki.de>
"""

import uuid
from django.db import models
from django.contrib import admin
from django.contrib.auth.models import User

AUTH_TOKEN_LENGTH = 8

def create_auth_token():
    """Creates a random hex number for use as an authorization token."""
    new_token = uuid.uuid4().hex[:AUTH_TOKEN_LENGTH]
    while (AuthToken.objects.filter(auth_token=new_token)):
        new_token = uuid.uuid4().hex[:AUTH_TOKEN_LENGTH]
    return new_token

class AuthToken(models.Model):
    """An AuthToken is associated with one user, and allows access to
    the dashboard Web API."""
    auth_token = models.CharField (
        max_length = AUTH_TOKEN_LENGTH,
        default = create_auth_token,
        unique = True,
        verbose_name = 'authentication token',
        help_text = 'A random hex key that allows access to the dashboard API.')
    user = models.ForeignKey (
        User,
        help_text = 'The user associated with this API key.' )
    enabled = models.BooleanField (
        default = True,
        help_text = 'A boolean indicating whether this key is valid.' )

    class Meta:
        '''Meta information about the AuthToken class.'''
        ordering = ["user"]
        verbose_name = 'Authentication Token'

    def __unicode__(self):
        """Returns a Unicode String representation of the AuthToken."""
        return self.user.username + ' - ' + self.auth_token

class AuthTokenAdmin(admin.ModelAdmin):
    '''Admin interface to the AuthToken class.'''
    list_display = ('auth_token', 'user', 'enabled')
    list_editable = ('enabled',)
    list_filter = ('enabled',)

admin.site.register(AuthToken, AuthTokenAdmin)
