#!/usr/bin/env python
# encoding: utf-8

# Copyright (C) 2022 Chintalagiri Shashank
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
httpx based www backend (:mod:`tendril.utils.www.hx`)
=====================================================

TODO Some introduction

This is added primarily for async support and interacting with internal APIs..

Features such as caching and proxy support are not presently implemented, but
should be. Note that both proxying and caching for the present intended
applications need exclusion/bypass mechanisms.

New code should preferentially use this backend when possible, and older code
using the other backend can be gradually moved here.

"""


from functools import wraps
from contextlib import asynccontextmanager
from httpx import AsyncClient
from .ssl import ssl_context

from tendril.config import SSL_NOVERIFY_HOSTS

from tendril.utils import log
logger = log.get_logger(__name__, log.DEFAULT)


@asynccontextmanager
async def async_client(*args, **kwargs):
    """
    Application executable code will typically only have to interact with this
    ``contextmanager``. It should use this to create a http client session,
    perform its tasks, whatever they may be, within this context, and then
    exit the context.

    The client provided by this context manager will (should. TODO) be configured
    appropriately as per the network settings in the tendril configuration.

    This client may also provide some caching and cache management functionality
    in the future, similar to the other tendril www providers.
    """
    try:
        if 'verify' in kwargs.keys():
            if not kwargs['verify']:
                if 'base_url' not in kwargs.keys():
                    logger.warn("SSL verification disabled for this generic httpx client!")
                else:
                    logger.info(f"SSL verification disabled for this httpx client to {kwargs['base_url']}")
                kwargs['verify'] = False
            else:
                raise NotImplementedError(
                    "A custom verify has been provided, but we already "
                    "specify a custom SSL context to manage self-signed "
                    "certificate verification. Merging the two contexts "
                    "is not presently implemented")
        elif 'base_url' in kwargs.keys() and kwargs['base_url'] in SSL_NOVERIFY_HOSTS:
            logger.info(f"SSL verification disabled for httpx client to {kwargs['base_url']}")
            kwargs['verify'] = False
        else:
            kwargs['verify'] = ssl_context
        async with AsyncClient(*args, **kwargs) as client:
            yield client
    finally:
        await client.aclose()


def with_async_client_cl(**client_kwargs):
    """
        Application executable code will typically only have to interact with this
        function or the :func:`async_client` ``contextmanager``. The
        :func:`with_async_client_cl` decorator is intended to decorate instance methods
        which require an async client and may be part of a large transaction.

        Such a function would accept 'client' only as a keyword argument
        ``client``, which can be an async client (created by :func:`async_client`)
        provided by the caller. If ``client`` is ``None``, this decorator creates
        a new client with the provided parameters  and calls the decorated
        function using it.

        .. seealso:: :func:`async_client`

        """
    def decorator(func):
        @wraps(func)
        async def inject_client(self, *args, **kwargs):
            client = kwargs.get('client', None)
            if client is None:
                ckw = {}
                if hasattr(self, '_async_http_client_args'):
                    ckw.update(self._client_args())
                ckw.update(client_kwargs)
                print("Using client kwargs", ckw)
                async with async_client(**ckw) as c:
                    kwargs['client'] = c
                    result = await func(self, *args, **kwargs)
                    return result
            else:
                result = await func(self, *args, **kwargs)
                return result
        return inject_client
    return decorator
