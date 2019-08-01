#!/usr/bin/env python
# encoding: utf-8

# Copyright (C) 2015-2019 Chintalagiri Shashank
#
# This file is part of tendril.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
urllib based www backend (:mod:`tendril.utils.www.bare`)
========================================================

TODO Some details about the other stuff

This module also provides the :class:`WWWCachedFetcher` class,
an instance of which is available in :data:`cached_fetcher`, which
is subsequently used by :func:`get_soup` and any application code
that wants cached results.

Overall, caching for this backend looks something like this :

- :class:`WWWCachedFetcher` provides short term (~5 days)
  caching, aggressively caching whatever goes through it. This
  caching is NOT HTTP1.1 compliant. In case HTTP1.1 compliant
  caching is desired, use the requests based implementation
  instead or use an external http-replicator like caching proxy.

- :class:`RedirectCacheHandler` is something of a special case,
  handling redirects which otherwise would be incredibly expensive.
  Unfortunately, this layer is also the dumbest cacher, and does
  not expire anything. Ever. To 'invalidate' something in this cache,
  the entire cache needs to be nuked. It may be worthwhile to consider
  moving this to redis instead.

"""

import six
import time
from hashlib import md5
from bs4 import BeautifulSoup
from six.moves.urllib.request import ProxyHandler
from six.moves.urllib.request import HTTPHandler, HTTPSHandler
from six.moves.urllib.request import build_opener
from six.moves.urllib.error import HTTPError, URLError

from tendril.config import NETWORK_PROXY_TYPE
from tendril.config import ENABLE_REDIRECT_CACHING
from tendril.config import MAX_AGE_DEFAULT

from .helpers import get_http_proxy_url
from .redirectcache import CachingRedirectHandler
from .redirectcache import get_actual_url
from .redirectcache import redirect_cache
from .caching import CacheBase
from .caching import WWW_CACHE
from .status import set_connected
from .status import set_disconnected

from tendril.utils import log
logger = log.get_logger(__name__, log.WARNING)


def _test_opener(openr):
    """
    Tests an opener obtained using :func:`urllib2.build_opener` by attempting
    to open Google's homepage. This is used to test internet connectivity.
    """
    try:
        openr.open('http://www.google.com', timeout=5)
        return True
    except URLError:
        return False


def _create_opener():
    """
    Creates an opener for the internet.

    It also attaches the :class:`CachingRedirectHandler` to the opener and
    sets its User-agent to ``Mozilla/5.0``.

    If the Network Proxy settings are set and recognized, it creates the
    opener and attaches the proxy_handler to it. The opener is tested and
    returned if the test passes.

    If the test fails an opener without the proxy settings is created instead
    and is returned instead.
    """
    use_proxy = False
    proxy_handler = None

    if NETWORK_PROXY_TYPE == 'http':
        use_proxy = True
        proxyurl = get_http_proxy_url()
        proxy_handler = ProxyHandler({'http': proxyurl,
                                      'https': proxyurl})
    if use_proxy:
        openr = build_opener(HTTPHandler(), HTTPSHandler(),
                             proxy_handler, CachingRedirectHandler)
    else:
        openr = build_opener(HTTPSHandler(), HTTPSHandler(),
                             CachingRedirectHandler)
    openr.addheaders = [('User-agent', 'Mozilla/5.0')]
    if _test_opener(openr):
        set_connected()
    else:
        set_disconnected()
    return openr


opener = _create_opener()


def urlopen(url):
    """
    Opens a url specified by the ``url`` parameter.

    This function handles redirect caching, if enabled.
    """
    # warnings.warn("urlopen() is a part of the urllib2 based www "
    #               "implementation and is deprecated.", DeprecationWarning)
    url = get_actual_url(url)
    try:
        page = opener.open(url)
        try:
            if ENABLE_REDIRECT_CACHING is True and page.status == 301:
                logger.debug('Detected New Permanent Redirect:\n' +
                             url + '\n' + page.url)
                redirect_cache[url] = page.url
        except AttributeError:
            pass
        return page
    except HTTPError as e:
        logger.error("HTTP Error : {0} {1}".format(e.code, url))
        raise
    except URLError as e:
        logger.error("URL Error : {0} {1}".format(e.errno, e.reason))
        raise


class WWWCachedFetcher(CacheBase):
    """
    Subclass of :class:`CacheBase` to handle catching of url ``fetch``
    responses.
    """
    def _get_filepath(self, url):
        """
        Return a filename constructed from the md5 sum of the url
        (encoded as ``utf-8`` if necessary).

        :param url: url of the resource to be cached
        :return: name of the cache file

        """
        # Use MD5 hash of the URL as the filename
        if six.PY3 or (six.PY2 and isinstance(url, unicode)):
            filepath = md5(url.encode('utf-8')).hexdigest()
        else:
            filepath = md5(url).hexdigest()
        return filepath

    def _get_fresh_content(self, url):
        """
        Retrieve a fresh copy of the resource from the source.

        :param url: url of the resource
        :return: contents of the resource

        """
        logger.debug('Getting url content : {0}'.format(url))
        time.sleep(1)
        return urlopen(url).read()

    def fetch(self, url, max_age=MAX_AGE_DEFAULT, getcpath=False):
        """
        Return the content located at the ``url`` provided. If a fresh cached
        version exists, it is returned. If not, a fresh one is obtained,
        stored in the cache, and returned.

        :param url: url of the resource to retrieve.
        :param max_age: maximum age in seconds.
        :param getcpath: (default False) if True, returns only the path to
                         the cache file.

        """
        # warnings.warn(
        #     "WWWCachedFetcher() is a part of the urllib2 based "
        #     "www implementation and is deprecated.",
        #     DeprecationWarning
        # )
        return self._accessor(max_age, getcpath, url)


#: The module's :class:`WWWCachedFetcher` instance which should be
#: used whenever cached results are desired. The cache is stored in
#: the directory defined by :data:`tendril.config.WWW_CACHE`.
cached_fetcher = WWWCachedFetcher(cache_dir=WWW_CACHE)


def get_soup(url):
    """
    Gets a :mod:`bs4` parsed soup for the ``url`` specified by the parameter.
    The :mod:`lxml` parser is used.
    This function returns a soup constructed of the cached page if one
    exists and is valid, or obtains one and dumps it into the cache if it
    doesn't.
    """
    page = cached_fetcher.fetch(url)
    if page is None:
        return None
    soup = BeautifulSoup(page, 'lxml')
    return soup

