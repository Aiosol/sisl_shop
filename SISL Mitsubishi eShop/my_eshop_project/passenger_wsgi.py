import os
import sys

# Add your project directory to sys.path
path = '/home/mitsubishifabd/apps/sisl_shop/SISL Mitsubishi eShop\my_eshop_project'
if path not in sys.path:
    sys.path.insert(0, path)

# Set environment variable for Django settings
os.environ['DJANGO_SETTINGS_MODULE'] = 'eshop_project.settings'

# Create WSGI application
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()