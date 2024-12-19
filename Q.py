#!/usr/bin/env python
import os
import sys
import logging
from backend.settings import LOGGING


def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc

    sys.argv = ["manage.py", "djangohuey"]
    logging.info("🚀 Starting queue server...")
    try:
        execute_from_command_line(sys.argv)
        logging.info("😉 Shutting down gracefully...")
    except Exception as e:
        logging.error(f"😰 Failed to start  queue server: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    import logging.config

    logging.config.dictConfig(LOGGING)
    main()
