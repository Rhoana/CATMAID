from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

CLASSIFICATION_PROJECT_ID = getattr(settings, 'CLASSIFICATION_PROJECT_ID', None)
if CLASSIFICATION_PROJECT_ID is None:
    raise ImproperlyConfigured("In order to use CATMAID's classification system "
        "you have to configure CLASSIFICATION_PROJECT_ID in your settings module.")

