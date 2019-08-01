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
Reusable minor helpers for www (:mod:`tendril.utils.www.helpers`)
=================================================================

TODO Some introduction

"""


from tendril.config import NETWORK_PROXY_TYPE
from tendril.config import NETWORK_PROXY_IP
from tendril.config import NETWORK_PROXY_PORT
from tendril.config import NETWORK_PROXY_USER
from tendril.config import NETWORK_PROXY_PASS

from tendril.utils import log
logger = log.get_logger(__name__, log.WARNING)


def get_http_proxy_url():
    """
    Constructs the proxy URL for HTTP proxies from relevant
    :mod:`tendril.config` Config options, and returns the URL string
    in the form:

        ``http://[NP_USER:NP_PASS@]NP_IP[:NP_PORT]``

    where NP_xxx is obtained from the :mod:`tendril.config` ConfigOption
    NETWORK_PROXY_xxx.
    """
    if NETWORK_PROXY_USER is None:
        proxyurl_http = 'http://' + NETWORK_PROXY_IP
    else:
        proxyurl_http = 'http://{0}:{1}@{2}'.format(NETWORK_PROXY_USER,
                                                    NETWORK_PROXY_PASS,
                                                    NETWORK_PROXY_IP)
    if NETWORK_PROXY_PORT:
        proxyurl_http += ':' + NETWORK_PROXY_PORT
    return proxyurl_http


def _get_proxy_dict():
    """
    Construct a dict containing the proxy settings in a format compatible
    with the :class:`requests.Session`. This function is used to construct
    the :data:`_proxy_dict`.

    """
    if NETWORK_PROXY_TYPE == 'http':
        proxyurl = get_http_proxy_url()
        return {'http': proxyurl,
                'https': proxyurl}
    else:
        return None


#: A dict containing the proxy settings in a format compatible
#: with the :class:`requests.Session`.
proxy_dict = _get_proxy_dict()


def strencode(string):
    """
    This function converts unicode strings to ASCII, using python's
    :func:`str.encode`, replacing any unicode characters present in the
    string. Unicode characters which Tendril expects to see in web content
    related to it are specifically replaced first with ASCII characters
    or character sequences which reasonably reproduce the original meanings.

    :param string: unicode string to be encoded.
    :return: ASCII version of the string.

    .. warning::
        This function is marked for deprecation by the general (but gradual)
        move towards ``unicode`` across tendril.

    """
    nstring = ''
    for char in string:
        if char == u'\u00b5':
            char = 'u'
        if char == u'\u00B1':
            char = '+/-'
        nstring += char
    return nstring.encode('ascii', 'replace')
