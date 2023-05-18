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
Redirect Caching Infrastructure (:mod:`tendril.utils.www.redirectcaching`)
==========================================================================

TODO Some introduction

"""


import os
import atexit

try:
    import cPickle as pickle
except ImportError:
    import pickle

from six.moves.urllib.request import HTTPRedirectHandler

from tendril.config import INSTANCE_CACHE
from tendril.config import ENABLE_REDIRECT_CACHING

from tendril.utils import log
logger = log.get_logger(__name__, log.WARNING)


REDIR_CACHE_FILE = os.path.join(INSTANCE_CACHE, 'redirects.p')


logger.info("Initializing Redirect Caching")
try:
    with open(REDIR_CACHE_FILE, "rb") as rdcf:
        redirect_cache = pickle.load(rdcf)
    logger.info('Loaded Redirect Cache from file')
except EOFError:
    os.remove(REDIR_CACHE_FILE)
    redirect_cache = {}
    logger.warning('Discarded Corrupt Redirect Cache')
except (IOError, FileNotFoundError):
    redirect_cache = {}
    logger.info('Created new Redirect Cache')


def dump_redirect_cache():
    """
    Called during python interpreter shutdown, this function dumps the
    redirect cache to the file system.
    """
    if DUMP_REDIR_CACHE_ON_EXIT:
        with open(REDIR_CACHE_FILE, 'wb') as f:
            pickle.dump(redirect_cache, f, protocol=2)
        logger.info('Dumping Redirect Cache to file')


if ENABLE_REDIRECT_CACHING:
    DUMP_REDIR_CACHE_ON_EXIT = True
else:
    DUMP_REDIR_CACHE_ON_EXIT = False

if ENABLE_REDIRECT_CACHING is True:
    atexit.register(dump_redirect_cache)


class CachingRedirectHandler(HTTPRedirectHandler):
    """
    This handler modifies the behavior of
    :class:`urllib2.HTTPRedirectHandler`, resulting in a HTTP ``301`` or
    ``302`` status to be included in the ``result``.

    When this handler is attached to a ``urllib2`` opener, if the opening of
    the URL resulted in a redirect via HTTP ``301`` or ``302``, this is
    reported along with the result. This information can be used by the opener
    to maintain a redirect cache.
    """
    def __init__(self):
        pass

    def http_error_301(self, req, fp, code, msg, headers):
        """
        Wraps the :func:`urllib2.HTTPRedirectHandler.http_error_301` handler,
        setting the ``result.status`` to ``301`` in case a http ``301`` error
        is encountered.
        """
        result = HTTPRedirectHandler.http_error_301(
            self, req, fp, code, msg, headers)
        result.status = code
        return result

    def http_error_302(self, req, fp, code, msg, headers):
        """
        Wraps the :func:`urllib2.HTTPRedirectHandler.http_error_302` handler,
        setting the ``result.status`` to ``302`` in case a http ``302`` error
        is encountered.
        """
        result = HTTPRedirectHandler.http_error_302(
            self, req, fp, code, msg, headers)
        result.status = code
        return result


def get_actual_url(url):
    # warnings.warn("get_actual_url() is a part of Redirect caching and is "
    #               "deprecated.", DeprecationWarning)
    if not ENABLE_REDIRECT_CACHING:
        return url
    else:
        while url in redirect_cache.keys():
            url = redirect_cache[url]
        return url
