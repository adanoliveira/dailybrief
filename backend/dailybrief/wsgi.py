"""
WSGI config for dailybrief project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/howto/deployment/wsgi/
"""

import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dailybrief.settings')

# Get the Django WSGI application
application = get_wsgi_application()

# Wrap the application for Vercel
def handler(request, **kwargs):
    return application(request, **kwargs)

# Make it work with Vercel
app = application
