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
suds based www SOAP backend (:mod:`tendril.utils.www.soap`)
===========================================================

TODO Some introduction

"""


import os
import six
import time
import logging
from hashlib import md5
from suds.client import Client
from suds.transport.http import HttpAuthenticated
from suds.transport.http import HttpTransport

try:
    import cPickle as pickle
except ImportError:
    import pickle

from .helpers import proxy_dict
from .caching import CacheBase

from tendril.config import INSTANCE_CACHE
from tendril.config import MAX_AGE_DEFAULT

from tendril.utils import log
logger = log.get_logger(__name__, log.WARNING)

logging.getLogger('suds.xsd.query').setLevel(logging.INFO)
logging.getLogger('suds.xsd.sxbasic').setLevel(logging.INFO)
logging.getLogger('suds.xsd.schema').setLevel(logging.INFO)
logging.getLogger('suds.xsd.sxbase').setLevel(logging.INFO)
logging.getLogger('suds.metrics').setLevel(logging.INFO)
logging.getLogger('suds.wsdl').setLevel(logging.INFO)
logging.getLogger('suds.client').setLevel(logging.INFO)
logging.getLogger('suds.resolver').setLevel(logging.INFO)
logging.getLogger('suds.umx.typed').setLevel(logging.INFO)
logging.getLogger('suds.mx.literal').setLevel(logging.INFO)
logging.getLogger('suds.mx.core').setLevel(logging.INFO)
logging.getLogger('suds.transport.http').setLevel(logging.INFO)

SOAP_CACHE = os.path.join(INSTANCE_CACHE, 'soapcache')


class ThrottledTransport(HttpAuthenticated):
    def __init__(self, **kwargs):
        """
        Provides a throttled HTTP transport for respecting rate limits
        on rate-restricted SOAP APIs using :mod:`suds`.

        This class is a :class:`suds.transport.Transport` subclass
        based on the default ``HttpAuthenticated`` transport.

        :param minimum_spacing: Minimum number of seconds between requests.
                                Default 0.
        :type minimum_spacing: int

        .. todo::
            Use redis or so to coordinate between threads to allow a
            maximum requests per hour/day limit.

        """
        self._minumum_spacing = kwargs.pop('minimum_spacing', 0)
        self._last_called = int(time.time())
        HttpTransport.__init__(self, **kwargs)

    def send(self, request):
        """
        Send a request and return the response. If the minimum number of
        seconds between requests have not yet elapsed, then the function
        sleeps for the remaining period and then passes the request along.
        """
        now = int(time.time())
        logger.debug('Getting SOAP response')
        tsincelast = now - self._last_called
        if tsincelast < self._minumum_spacing:
            tleft = self._minumum_spacing - tsincelast
            logger.info("Throttling SOAP client for {0}".format(tleft))
            time.sleep(tleft)
        self._last_called = now
        return HttpAuthenticated.send(self, request)


class CachedTransport(CacheBase, HttpAuthenticated):
    def __init__(self, **kwargs):
        """
        Provides a cached HTTP transport with request-based caching for
        SOAP APIs using :mod:`suds`.

        This is a subclass of :class:`CacheBase` and the default
        ``HttpAuthenticated`` transport.

        :param cache_dir: folder where the cache is located.
        :param max_age: the maximum age in seconds after which a response
                        is considered stale.

        """
        cache_dir = kwargs.pop('cache_dir')
        self._max_age = kwargs.pop('max_age', MAX_AGE_DEFAULT)
        CacheBase.__init__(self, cache_dir=cache_dir)

    def _get_filepath(self, request):
        """
        Return a filename constructed from the md5 hash of a
        combination of the request URL and message content
        (encoded as ``utf-8`` if necessary).

        :param request: the request object for which a cache filename
                        is needed.
        :return: name of the cache file.

        """
        keystring = request.url + request.message
        if six.PY3 or (six.PY2 and isinstance(keystring, unicode)):  # noqa
            filepath = md5(keystring.encode('utf-8')).hexdigest()
        else:
            filepath = md5(keystring).hexdigest()
        return filepath

    def _get_fresh_content(self, request):
        """
        Retrieve a fresh copy of the resource from the source.

        :param request: the request object for which the response
                        is needed.
        :return: the response to the request

        """
        response = HttpAuthenticated.send(self, request)
        return response

    @staticmethod
    def _serialize(response):
        """
        Serializes the suds response object using :mod:`cPickle`.

        If the response has an error status (anything other than
        200), raises ``ValueError``. This is used to avoid caching
        errored responses.

        """
        if response.code != 200:
            logger.debug("Bad Status {0}".format(response.code))
            raise ValueError
        return pickle.dumps(response)

    @staticmethod
    def _deserialize(filecontent):
        """
        De-serializes the cache content into a suds response object
        using :mod:`cPickle`.

        """
        return pickle.loads(filecontent)

    def send(self, request):
        """
        Send a request and return the response. If a fresh response to the
        request is available in the cache, that is returned instead. If it
        isn't, a fresh response is obtained, cached, and returned.

        """
        response = self._accessor(self._max_age, False, request)
        return response


class CachedThrottledTransport(ThrottledTransport, CachedTransport):
    def __init__(self, **kwargs):
        """
        A cached HTTP transport with both throttling and request-based
        caching for SOAP APIs using :mod:`suds`.

        This is a subclass of :class:`CachedTransport` and
        :class:`ThrottledTransport`.

        Keyword arguments not handled here are passed on via
        :class:`ThrottledTransport` to :class:`HttpTransport`.

        :param cache_dir: folder where the cache is located.
        :param max_age: the maximum age in seconds after which a response
                        is considered stale.
        :param minimum_spacing: Minimum number of seconds between requests.
                                Default 0.
        """
        cache_dir = kwargs.pop('cache_dir')
        max_age = kwargs.pop('max_age', MAX_AGE_DEFAULT)
        CachedTransport.__init__(self, cache_dir=cache_dir, max_age=max_age)
        ThrottledTransport.__init__(self, **kwargs)

    def _get_fresh_content(self, request):
        """
        Retrieve a fresh copy of the resource from the source via
        :func:`ThrottledTransport.send`.

        :param request: the request object for which the response
                        is needed.
        :return: the response to the request

        """
        response = ThrottledTransport.send(self, request)
        return response

    def send(self, request):
        """
        Send a request and return the response, using
        :func:`CachedTransport.send`.

        """
        return CachedTransport.send(self, request)


def get_soap_client(wsdl, cache_requests=True,
                    max_age=MAX_AGE_DEFAULT, minimum_spacing=0):
    """
    Creates and returns a suds/SOAP client instance bound to the
    provided ``WSDL``. If ``cache_requests`` is True, then the
    client is configured to use a :class:`CachedThrottledTransport`.
    The transport is constructed to use :data:`SOAP_CACHE` as the
    cache folder, along with the ``max_age`` and ``minimum_spacing``
    parameters if provided.

    If ``cache_requests`` is ``False``, the client uses the default
    :class:`suds.transport.http.HttpAuthenticated` transport.
    """
    if cache_requests is True:
        if proxy_dict is None:
            soap_transport = CachedThrottledTransport(
                cache_dir=SOAP_CACHE, max_age=max_age,
                minimum_spacing=minimum_spacing,
            )
        else:
            soap_transport = CachedThrottledTransport(
                cache_dir=SOAP_CACHE, max_age=max_age,
                minimum_spacing=minimum_spacing,
                proxy=proxy_dict,
            )
    else:
        if proxy_dict is None:
            soap_transport = HttpAuthenticated()
        else:
            soap_transport = HttpAuthenticated(proxy=proxy_dict)
    return Client(wsdl, transport=soap_transport)
