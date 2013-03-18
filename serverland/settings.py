# Django settings for serverland project.
"""
Project: MT Server Land
 Author: Christian Federmann <cfedermann@gmail.com>
"""
import os
ROOT_PATH = os.getcwd()
DEPLOYMENT_PREFIX = '/mt-serverland'

from subprocess import check_output
try:
    commit_log = check_output(['git', 'log', '--pretty=oneline'])
    # pylint: disable-msg=E1103
    COMMIT_TAG = commit_log.split('\n')[0].split()[0]

# pylint: disable-msg=W0703
except Exception, e:
    COMMIT_TAG = None

# Serialized message files will be stored in this location.
TRANSLATION_MESSAGE_PATH = '{0}/messages'.format(ROOT_PATH)

# Assert that TRANSLATION_MESSAGE_PATH actually exists.
assert os.path.exists(TRANSLATION_MESSAGE_PATH), \
  "Folder {0} does not exist!".format(TRANSLATION_MESSAGE_PATH)

import logging
from logging.handlers import RotatingFileHandler

# Logging settings for this Django project.
LOG_LEVEL = logging.DEBUG
LOG_FILENAME = '/tmp/serverland.log'
LOG_FORMAT = "[%(asctime)s] %(name)s::%(levelname)s %(message)s"
LOG_DATE = "%m/%d/%Y @ %H:%M:%S"
LOG_FORMATTER = logging.Formatter(LOG_FORMAT, LOG_DATE)

LOG_HANDLER = RotatingFileHandler(filename=LOG_FILENAME, mode="a",
  maxBytes=1024*1024, backupCount=5, encoding="utf-8")
LOG_HANDLER.setLevel(level=LOG_LEVEL)
LOG_HANDLER.setFormatter(LOG_FORMATTER)

LOGIN_URL = '{0}/login/'.format(DEPLOYMENT_PREFIX)
LOGIN_REDIRECT_URL = '{0}/'.format(DEPLOYMENT_PREFIX)
LOGOUT_URL = '{0}/logout/'.format(DEPLOYMENT_PREFIX)

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    # ('Your Name', 'your_email@domain.com'),
)

MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': '{}/development.db'.format(ROOT_PATH),
    }
}

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'Europe/Berlin'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = '{0}/media/'.format(ROOT_PATH)

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = ''

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = '{0}/media/'.format(DEPLOYMENT_PREFIX)

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'fw341l^lu!z7^@&9idq+7$a+b-l*ph_4^1#aj+%+o556fdsu3!'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
#     'django.template.loaders.eggs.Loader',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
)

ROOT_URLCONF = 'serverland.urls'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    '{0}/templates'.format(ROOT_PATH),
)

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.contrib.auth.context_processors.auth',
    'django.contrib.messages.context_processors.messages',
)

MESSAGE_STORAGE = 'django.contrib.messages.storage.session.SessionStorage'

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.admin',
    'django.contrib.messages',

    'serverland.dashboard',
    'serverland.dashboard.api',
)
