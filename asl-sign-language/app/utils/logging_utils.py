import logging
import warnings


def configure_logging():
    warnings.filterwarnings("ignore")
    logging.basicConfig(level=logging.INFO, format="[server] %(message)s")
    return logging.getLogger(__name__)


def get_logger(name):
    return logging.getLogger(name)
