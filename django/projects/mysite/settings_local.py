# If you don't have settings.py in this directory, you should copy
# this file to settings.py and customize it.

from settings_base import *
import sys, os
import djcelery

DATABASES = {
    'default': {
        'ENGINE': 'custom_postgresql_psycopg2', # Add 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': 'catmaid-local',      # Or path to database file if using sqlite3.
        'USER': 'catmaid_user',  # Not used with sqlite3.
        'PASSWORD': 'catmaid_user_password',  # Not used with sqlite3.
        'HOST': '',                           # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '',                           # Set to empty string for default. Not used with sqlite3.
    }
}

DEBUG = True
TEMPLATE_DEBUG = DEBUG

# Make this unique, and don't share it with anybody.
# (You can generate a key with:
# >>> from random import choice
# >>> ''.join([choice('abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)') for i in range(50)])
# '@er^vm3$w#9n$)z3avny*hh+l^#ezv+sx*(72qwp0c%%cg1$i+'
# ... which is how "django-admin startproject" does it.)
SECRET_KEY = 'sadpoijxcvpoiajfasdpfoiadjf'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    relative('..', '..', 'templates')
)

# Absolute path to the directory that holds user generated data
# like cropped microstacks. Make sure this folder is writable by
# the user running the webserver (and Celery if croppish should
# be used).
# Example: "/var/www/example.org/media/"
MEDIA_ROOT = relative('..', '..', 'media_root')

# URL that gives access to files stored in MEDIA_ROOT (managed stored
# files). It must end in a slash if set to a non-empty value.
# Example: "http://media.example.org/"
MEDIA_URL = '/media/'

# Static path to store generated NeuroHDF files (needs to be writable)
# as subdirectory of MEDIA_ROOT.
MEDIA_HDF5_SUBDIRECTORY = 'hdf5'
mkdir_p(os.path.join(MEDIA_ROOT, MEDIA_HDF5_SUBDIRECTORY))

# Static path to store cropped (needs to be writable) as subdirectory
# of MEDIA_ROOT.
MEDIA_CROPPING_SUBDIRECTORY = 'cropped'
mkdir_p(os.path.join(MEDIA_ROOT, MEDIA_CROPPING_SUBDIRECTORY))

# The URL where static files can be accessed, relative to the domain's root
STATIC_URL = '/static/'
# The absolute local path where the static files get collected to
STATIC_ROOT = relative('..', '..', 'static')

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'Europe/London'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-gb'

# Usually, CATMAID's Django back-end is not accessible on a domain's
# root ('/'), but rather a sub-directory like 'dj'. This might even be
# 'catmaid/dj' if catmaid is on a sub-directory as well. Django needs
# to know about this relative path and some web and WSGI servers pass
# this information to Django automatically (e.g. Apache + mod_wsgi).
# However, some don't (e.g. Nginx + Gevent) and the easiest way to
# tell Django were it lives is with the help of the FORCE_SCRIPT_NAME
# variable. It must not have a trailing slash.
# FORCE_SCRIPT_NAME = '/dj'

# Settings relative to the Apache subfolder
CATMAID_URL = '/'

# Local path to store HDF5 files
# File name convention: {projectid}_{stackid}.hdf
HDF5_STORAGE_PATH = relative('..', '..', 'hdf5')

# Define the URL of your CATMAIDs Django instance as it should appear in
# front of all Django related URLs.
CATMAID_DJANGO_URL = '/'

# Importer settings
# If you want to use the importer, please adjust these settings. The
# CATMAID_IMPORT_PATH in (and below) the importer should look for new
# data. The CATMAID_IMPORT_URL refers is the URL as seen from outside
# that gives read access to the CATMAID_IMPORT_PATH.
CATMAID_IMPORT_PATH = '/home/mark/catmaid9-south/httpdocs/data'
CATMAID_IMPORT_URL = 'CATMAIDURL/data'

## Celery configuration
djcelery.setup_loader()
CELERYD_CONCURRENCY = 1
# Simple django-kumbo message broker
INSTALLED_APPS += ("djkombu",)
BROKER_BACKEND = "djkombu.transport.DatabaseTransport"
