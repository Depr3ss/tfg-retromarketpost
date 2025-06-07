"""
WSGI config for TFG_Proy project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/wsgi/
"""

import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'TFG_Proy.settings')

application = get_wsgi_application()

# Ejecutar migraciones automáticamente al iniciar la app (útil en entornos sin shell)
from django.core.management import call_command

try:
    call_command('migrate', interactive=False)
except Exception as e:
    # Puedes quitar o modificar el print para evitar que se muestre en producción
    print(f"Error al ejecutar migraciones: {e}")
