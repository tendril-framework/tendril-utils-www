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
requests based www backend (:mod:`tendril.utils.www.bare`)
==========================================================

TODO Some introduction

"""

import os
import logging
import requests
from cachecontrol import CacheControlAdapter
from cachecontrol.caches import FileCache
from cachecontrol.heuristics import ExpiresAfter
from bs4 import BeautifulSoup

from tendril.config import INSTANCE_CACHE
from tendril.config import MAX_AGE_DEFAULT

from .helpers import proxy_dict

from tendril.utils import log

logger = log.get_logger(__name__, log.WARNING)

logging.getLogger('cachecontrol.controller').setLevel(logging.INFO)
logging.getLogger('requests.packages.urllib3.connectionpool').\
    setLevel(logging.WARNING)

REQUESTS_CACHE = os.path.join(INSTANCE_CACHE, 'requestscache')


#: The module's :class:`cachecontrol.caches.FileCache` instance which
#: should be used whenever cached :mod:`requests` responses are desired.
#: The cache is stored in the directory defined by
#: :data:`tendril.config.REQUESTS_CACHE`.
#: This cache uses very weak permissions. These should probably be
#: fine tuned.
requests_cache = FileCache(REQUESTS_CACHE, filemode=0o666, dirmode=0o777)


def _get_requests_cache_adapter(heuristic):
    """
    Given a heuristic, constructs and returns a
    :class:`cachecontrol.CacheControlAdapter` attached to the instance's
    :data:`requests_cache`.

    """
    return CacheControlAdapter(
        cache=requests_cache,
        heuristic=heuristic,
        cache_etags=False
    )


def get_session(target='http://', heuristic=None):
    """
    Gets a pre-configured :mod:`requests` session.

    This function configures the following behavior into the session :

    - Proxy settings are added to the session.
    - It is configured to use the instance's :data:`requests_cache`.
    - Permanent redirect caching is handled by :mod:`CacheControl`.
    - Temporary redirect caching is not supported.

    Each module / class instance which uses this should subsequently
    maintain it's own session with whatever modifications it requires
    within a scope which makes sense for the use case (and probably close
    it when it's done).

    The session returned from here uses the instance's REQUESTS_CACHE with
    a single - though configurable - heuristic. If additional caches or
    heuristics need to be added, it's the caller's problem to set them up.

    .. note::
        The caching here seems to be pretty bad, particularly for digikey
        passive component search. I don't know why.

    :param target: Defaults to ``'http://'``. string containing a prefix
                   for the targets that should be cached. Use this to setup
                   site-specific heuristics.
    :param heuristic: The heuristic to use for the cache adapter.
    :type heuristic: :class:`cachecontrol.heuristics.BaseHeuristic`
    :rtype: :class:`requests.Session`

    """

    s = requests.session()
    if proxy_dict is not None:
        s.proxies.update(proxy_dict)
    if heuristic is None:
        heuristic = ExpiresAfter(seconds=MAX_AGE_DEFAULT)
    s.mount(target, _get_requests_cache_adapter(heuristic))
    return s


def get_soup_requests(url, session=None):
    """
    Gets a :mod:`bs4` parsed soup for the ``url`` specified by the parameter.
    The :mod:`lxml` parser is used.

    If a ``session`` (previously created from :func:`get_session`) is
    provided, this session is used and left open. If it is not, a new session
    is created for the request and closed before the soup is returned.

    Using a caller-defined session allows re-use of a single session across
    multiple requests, therefore taking advantage of HTTP keep-alive to
    speed things up. It also provides a way for the caller to modify the
    cache heuristic, if needed.

    Any exceptions encountered will be raised, and are left for the caller
    to handle. The assumption is that a HTTP or URL error is going to make
    the soup unusable anyway.

    """
    if session is None:
        session = get_session()
        _close_after = True
    else:
        _close_after = False

    r = session.get(url)
    r.raise_for_status()
    soup = BeautifulSoup(r.content, 'lxml', from_encoding=r.encoding)

    if _close_after is True:
        session.close()
    return soup
