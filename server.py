import logging
from class_server import HTTPServer


logging.basicConfig(level=logging.INFO)


if __name__ == '__main__':
    logger = logging.getLogger("Server")
    try:
        print("Enter \\c to stop")
        HTTPServer(('localhost', 4890)).run()
    except KeyboardInterrupt:
        logger.info("Stop")
