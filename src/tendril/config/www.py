

from tendril.utils.config import ConfigOption
from tendril.utils import log
logger = log.get_logger(__name__, log.DEFAULT)

depends = ['tendril.config.core']


config_elements_network_caching = [
    ConfigOption(
        'ENABLE_REDIRECT_CACHING',
        "False",
        "Whether or not to cache 301 and 302 redirects. "
        "This probably works just fine, but treat it as a largely "
        "deprecated feature."
    ),
    ConfigOption(
        'MAX_AGE_DEFAULT',
        '600000',
        'Default max_age for data originating from www.'
    ),
]


config_elements_proxy = [
    ConfigOption(
        'NETWORK_PROXY_TYPE',
        "None",
        "The type of proxy to use. 'http' for squid/http, 'None' for none."
        "No other proxy types presently supported."
    ),
    ConfigOption(
        'NETWORK_PROXY_IP',
        "None",
        "The proxy server IP address."
    ),
    ConfigOption(
        'NETWORK_PROXY_PORT',
        "3128",
        "The proxy server port."
    ),
    ConfigOption(
        'NETWORK_PROXY_USER',
        "None",
        "The username to authenticate with the proxy server."
    ),
    ConfigOption(
        'NETWORK_PROXY_PASS',
        "None",
        "The password to authenticate with the proxy server."
    ),
]


config_elements_ssl = [
    ConfigOption(
        'CA_BUNDLE',
        "None",
        "Path to a custom CA certificate bundle to use. This is "
        "presently only used by the httpx backend"
    ),
    ConfigOption(
        'SSL_NOVERIFY_HOSTS',
        "[]",
        "List of domains in the form 'https://<domain>' for which "
        "SSL verification is to be skipped. This is intended for "
        "development purposes only."
    ),
]


def load(manager):
    logger.debug("Loading {0}".format(__name__))
    manager.load_elements(config_elements_network_caching,
                          doc="Network Caching Behavior Configuration")
    manager.load_elements(config_elements_proxy,
                          doc="Network Proxy Configuration")
    manager.load_elements(config_elements_ssl,
                          doc="SSL Client Configuration")
