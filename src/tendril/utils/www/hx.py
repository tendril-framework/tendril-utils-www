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


from contextlib import asynccontextmanager
from httpx import AsyncClient
from .ssl import ssl_context
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
        else:
            kwargs['verify'] = ssl_context
        async with AsyncClient(*args, **kwargs) as client:
            yield client
    finally:
        await client.aclose()
