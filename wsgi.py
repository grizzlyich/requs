"""
Root WSGI entrypoint for Vercel.

Vercel Python Runtime ищет переменную app в wsgi.py/asgi.py.
Локальный Django при этом продолжает использовать request_tracker/wsgi.py.
"""
import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "request_tracker.settings")

application = get_wsgi_application()
app = application
