from waitress import serve
from backend.wsgi import application
from backend.settings import LOGGING
import logging
from waitress.server import create_server
import sys
import signal


def shutdown_server(server, signum, frame):
    logging.info("😉 Shutting down gracefully...")
    server.close()
    sys.exit(0)


if __name__ == "__main__":
    logging.config.dictConfig(LOGGING)

    try:
        server = create_server(application, host="127.0.0.1", port=8888)
        signal.signal(signal.SIGTERM, lambda s, f: shutdown_server(server, s, f))
        signal.signal(signal.SIGINT, lambda s, f: shutdown_server(server, s, f))
        logging.info("✨ PhenoTools computation server started successfully...")
        server.run()
    except Exception as e:
        logging.error(
            f"😰 PhenoTools computation server error: {str(e)}", exc_info=True
        )
        sys.exit(1)
