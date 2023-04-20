

import ssl
from tendril.config import CA_BUNDLE
from tendril.utils import log
logger = log.get_logger(__name__, log.DEFAULT)


ssl_context = ssl.create_default_context()

if CA_BUNDLE:
    logger.info(f"Using custom CA Bundle at '{CA_BUNDLE}'")
    ssl_context.load_verify_locations(cafile=CA_BUNDLE)
