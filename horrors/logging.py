import logging
import sys


logger = logging.getLogger('horrors')
formatter = {
    logging.DEBUG: logging.Formatter('%(name)s %(levelname)s [%(asctime)s] %(message)s'),
    logging.INFO: logging.Formatter('[%(asctime)s] %(message)s')
}
handler = logging.StreamHandler(sys.stdout)
logger.addHandler(handler)


def info(msg):
    logger.info(msg)


def debug(msg):
    logger.debug(msg)


def error(msg):
    logger.error(msg)


def init(loglevel):
    handler.setLevel(loglevel)
    logger.setLevel(loglevel)
    handler.setFormatter(formatter[loglevel])
