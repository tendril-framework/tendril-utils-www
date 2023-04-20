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
Reusable Caching Primitives (:mod:`tendril.utils.www.caching`)
==============================================================

TODO Some introduction

"""


import os
import time
import codecs
import tempfile

from fs import open_fs
from fs.copy import copy_file
from fs.osfs import OSFS
from tendril.utils.fsutils import temp_fs
from tendril.config import INSTANCE_CACHE

from .status import is_connected

from tendril.utils import log
logger = log.get_logger(__name__, log.WARNING)

WWW_CACHE = os.path.join(INSTANCE_CACHE, 'soupcache')


class CacheBase(object):
    def __init__(self, cache_dir=WWW_CACHE):
        """
        This class implements a simple filesystem cache which can be used
        to create and obtain from various cached requests from internet
        resources.

        The cache is stored in the folder defined by ``cache_dir``, with a
        filename constructed by the :func:`_get_filepath` function.

        If the cache's :func:`_accessor` function is called with the
        ``getcpath`` attribute set to True, only the path to a (valid) file
        in the cache filesystem is returned, and opening and reading
        the file is left to the caller. This hook is provided to help deal
        with file encoding on a somewhat case-by-case basis, until the
        overall encoding problems can be ironed out.
        """
        self.cache_fs = open_fs(cache_dir, create=True)

    def _get_filepath(self, *args, **kwargs):
        """
        Given the parameters necessary to obtain the resource in normal
        circumstances, return a hash which is usable as the filename for
        the resource in the cache.

        The filename must be unique for every resource, and filename
        generation must be deterministic and repeatable.

        Must be implemented in every subclass.
        """
        raise NotImplementedError

    def _get_fresh_content(self, *args, **kwargs):
        """
        Given the parameters necessary to obtain the resource in normal
        circumstances, obtain the content of the resource from the source.

        Must be implemented in every subclass.
        """
        raise NotImplementedError

    @staticmethod
    def _serialize(response):
        """
        Given a response (as returned by :func:`_get_fresh_content`), convert
        it into a string which can be stored in a file. Use this function to
        serialize structured responses when needed.

        Unless overridden by the subclass, this function simply returns the
        response unaltered.

        The actions of this function should be reversed by
        :func:`_deserialize`.
        """
        return response

    @staticmethod
    def _deserialize(filecontent):
        """
        Given the contents of a cache file, reconstruct the original response
        in the original format (as returned by :func:`_get_fresh_content`).
        Use this function to deserialize cache files for structured responses
        when needed.

        Unless overridden by the subclass, this function simply returns the
        file content unaltered.

        The actions of this function should be reversed by
        :func:`_serialize`.
        """
        return filecontent

    def _cached_exists(self, filepath):
        return self.cache_fs.exists(filepath)

    def _is_cache_fresh(self, filepath, max_age):
        """
        Given the path to a file in the cache and the maximum age for the
        cache content to be considered fresh, returns (boolean) whether or
        not the cache contains a fresh copy of the response.

        :param filepath: Path to the filename in the cache corresponding to
                         the request, as returned by :func:`_get_filepath`.
        :param max_age: Maximum age of fresh content, in seconds.

        """
        if self._cached_exists(filepath):
            tn = int(time.time())
            tc = int(time.mktime(
                self.cache_fs.getinfo(filepath)['modified_time'].timetuple())
            )
            if tn - tc < max_age:
                return True
        return False

    def _accessor(self, max_age, getcpath=False, *args, **kwargs):
        """
        The primary accessor for the cache instance. Each subclass should
        provide a function which behaves similarly to that of the original,
        un-cached version of the resource getter. That function should adapt
        the parameters provided to it into the form needed for this one, and
        let this function maintain the cached responses and handle retrieval
        of the response.

        If the module's :data:`_internet_connected` is set to False, the
        cached value is returned regardless.

        """
        filepath = self._get_filepath(*args, **kwargs)
        send_cached = False
        if not is_connected() and self._cached_exists(filepath):
            send_cached = True
        if self._is_cache_fresh(filepath, max_age):
            logger.debug("Cache HIT")
            send_cached = True
        if send_cached is True:
            if getcpath is False:
                try:
                    filecontent = self.cache_fs.open(filepath, 'rb').read()
                    return self._deserialize(filecontent)
                except UnicodeDecodeError:
                    # TODO This requires the cache_fs to be a local
                    # filesystem. This may not be very nice. A way
                    # to hook codecs upto to pyfilesystems would be better
                    with codecs.open(
                            self.cache_fs.getsyspath(filepath),
                            encoding='utf-8') as f:
                        filecontent = f.read()
                        return self._deserialize(filecontent)
            else:
                return self.cache_fs.getsyspath(filepath)

        logger.debug("Cache MISS")
        data = self._get_fresh_content(*args, **kwargs)

        sdata = self._serialize(data)
        fd, temppath = tempfile.mkstemp()
        fp = os.fdopen(fd, 'wb')
        fp.write(sdata)
        fp.close()
        logger.debug("Creating new cache entry")
        # This can be pretty expensive if the move is across a real
        # filesystem boundary. We should instead use a temporary file
        # in the cache_fs itself
        try:
            copy_file(temp_fs, temp_fs.unsyspath(temppath),
                      self.cache_fs, filepath)
            if isinstance(self.cache_fs, OSFS):
                # TODO Refine permissions
                os.chmod(self.cache_fs.getsyspath(filepath), 0o666)
        except (KeyboardInterrupt, SystemExit):
            raise
        except:  # noqa
            logger.warning("Unable to write cache file "
                           "{0}".format(filepath))

        if getcpath is False:
            return data
        else:
            return self.cache_fs.getsyspath(filepath)
