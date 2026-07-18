"""
Arranque del servidor TPV Cafeteria con LiveReload
Uso: python run.py
"""
import os
import sys

if __name__ == '__main__':
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cafe_tpv.settings')

    from django.core.management import execute_from_command_line

    sys.argv = [sys.argv[0], 'runserver', '0.0.0.0:8080', '--noreload']
    execute_from_command_line(sys.argv)
