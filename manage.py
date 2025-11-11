#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Django's command-line utility for administrative tasks."""
import os
import sys


def main():
    # Set UTF-8 encoding for Windows console
    if sys.platform == 'win32':
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')
    """Run administrative tasks."""
    # Ensure repository root is first on sys.path and purge stale entries
    base_dir = os.path.dirname(os.path.abspath(__file__))
    if base_dir not in sys.path:
        sys.path.insert(0, base_dir)
    # Remove any entries pointing to a previous 'backend' folder or non-existent paths
    cleaned = []
    for p in sys.path:
        try:
            if not p:
                continue
            norm = os.path.normpath(p)
            if norm.lower().endswith(os.sep + 'backend'):
                continue
            if not os.path.exists(norm):
                continue
            cleaned.append(p)
        except Exception:
            # If anything goes wrong, skip that entry
            continue
    sys.path[:] = cleaned
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clinic.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
