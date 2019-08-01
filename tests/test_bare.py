#!/usr/bin/env python
# encoding: utf-8

# Copyright (C) 2015 Chintalagiri Shashank
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
Docstring for test_utils_www
"""

import six
from tendril.utils.www import redirectcache
from tendril.utils.www import bare
from hashlib import md5
import pytest
from six.moves.urllib.error import HTTPError, URLError
redirectcache.DUMP_REDIR_CACHE_ON_EXIT = False


def test_cached_fetcher():
    test_url = 'http://www.google.com'
    if six.PY3:
        filepath = md5(test_url.encode('utf-8')).hexdigest()
    else:
        filepath = md5(test_url).hexdigest()
    fs = bare.cached_fetcher.cache_fs
    if fs.exists(filepath):
        fs.remove(filepath)
    soup = bare.get_soup('http://www.google.com')
    assert soup is not None
    assert fs.exists(filepath)


def test_www_errors():
    with pytest.raises(HTTPError):
        bare.get_soup('http://httpstat.us/404')
    with pytest.raises(URLError):
        bare.get_soup('httpd://httpstat.us/404')
    result = bare.urlopen('http://httpstat.us/500')
    assert result is None
