#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# This file is part of the Wapiti project (https://wapiti.sourceforge.io)
# Copyright (C) 2006-2021 Nicolas SURRIBAS
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
import sys
from functools import partial

from loguru import logger as logging

logging.remove()
# logging.debug is 10
logging.level("VERBOSE", no=15)
# logging.info is 20
logging.level("BLUE", no=21, color="<blue>")
logging.level("GREEN", no=22, color="<green>")
# logging.success is 25
# logging.warning is 30
logging.level("ORANGE", no=35, color="<yellow>")
# logging.error is 40
logging.level("RED", no=45, color="<red>")
# logging.critical is 50

log_blue = partial(logging.log, "BLUE")
log_green = partial(logging.log, "GREEN")
log_red = partial(logging.log, "RED")
log_orange = partial(logging.log, "ORANGE")
log_verbose = partial(logging.log, "VERBOSE")

# Set default logging
logging.add(sys.stdout, colorize=False, format="{message}", level="INFO")
