"""
WSGI config for request_tracker project.
"""
import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "request_tracker.settings")

application = get_wsgi_application()
app = application
