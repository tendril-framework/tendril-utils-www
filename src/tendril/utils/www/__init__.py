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
The WWW Utils Module (:mod:`tendril.utils.www`)
===============================================

This module provides utilities to deal with the internet. All application code
should access the internet through this module, since this where support for
proxies and caching is implemented.

This module provides three main approaches to handling access to internet
resources :

.. rubric:: urllib based access (``tendril.utils.www.bare``)

.. autosummary::

    urlopen
    get_soup
    cached_fetcher

.. rubric:: requests based access (``tendril.utils.www.req``)

.. autosummary::

    get_soup_requests
    get_session

.. rubric:: suds based SOAP access (``tendril.utils.www.soap``)

.. autosummary::

    get_soap_client

Caching Strategies
------------------

The backends provided by these modules have integrated caching mechanisms
built-in to speed up access to internet based resources.

.. rubric:: Redirect Caching

Redirect caching speeds up network accesses by saving ``301`` and ``302``
redirects, and not needing to get the correct URL on a second access. This
redirect cache is stored as a pickled object in the ``INSTANCE_CACHE``
folder. The effect of this caching is far more apparent when a replicator
cache is also used.

Redirect caching is only supported by the urllib based backend
(``tendril.utils.www.bare``), and is likely going to be phased out
entirely in the future.

.. rubric:: Full Response Caching

This is a more typical kind of caching, which uses a backend-dependent
mechanism to maintain a cache of full responses received.


WWW Access Backends
-------------------

.. toctree::

   tendril.utils.www.bare
   tendril.utils.www.req
   tendril.utils.www.soap


Other WWW Utilities and Backend Helpers
---------------------------------------

.. toctree::

   tendril.utils.www.helpers
   tendril.utils.www.caching
   tendril.utils.www.redirectcaching
   tendril.utils.www.status


.. todo::
    Consider replacing uses of urllib/urllib2 backend with
    :mod:`requests` and simplify this module. Currently, the
    cache provided with the ``requests`` implementation here
    is the major bottleneck and seems to cause a major
    performance hit.

"""

from .helpers import strencode

# Bare urllib based access
from .bare import urlopen
from .bare import cached_fetcher
from .bare import get_soup

# Requests based access
from .req import get_session
from .req import get_soup_requests

# suds based SOAP access
from .soap import get_soap_client
