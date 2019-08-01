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
Internet Connection Status (:mod:`tendril.utils.www.status`)
============================================================

This module only really exists to pull the _internet_connected flag out
from the core modules, since it is actually shared between them. The
original form would have caused annoying import loops when the www module
was split up. A simpler solution probably exists, and should be moved to.

"""


_internet_connected = False


def is_connected():
    global _internet_connected
    return _internet_connected


def set_connected():
    global _internet_connected
    _internet_connected = True


def set_disconnected():
    global _internet_connected
    _internet_connected = False
