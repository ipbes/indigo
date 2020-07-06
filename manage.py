#!/usr/bin/env python
import os
import sys

if __name__ == '__main__':
    if os.environ.get('DJANGO_ENV') == 'production':
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'indigo.production')
    else:
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'indigo.settings')

    from django.core.management import execute_from_command_line
    
    execute_from_command_line(sys.argv)