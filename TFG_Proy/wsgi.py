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

from django.core.management import call_command
from django.db.utils import OperationalError
import sys

def run_migrations_and_load_data():
    try:
        # Aplica migraciones
        call_command('migrate', interactive=False)
        
        # Importar modelos necesarios para comprobar si cargar datos
        from market.models import Producto  # ajusta según tu app
        
        # Comprueba si hay datos, si no los carga
        if Producto.objects.count() == 0:
            print("Cargando datos iniciales...")
            call_command('loaddata', 'datos.json')
        else:
            print("Datos ya existentes, no se cargan de nuevo.")
            
        # Recoge archivos estáticos
        call_command('collectstatic', '--noinput')
        
    except OperationalError as e:
        print(f"Error de base de datos al migrar o cargar datos: {e}")
    except Exception as e:
        print(f"Error general: {e}", file=sys.stderr)

run_migrations_and_load_data()
