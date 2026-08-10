#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# This file is part of the Wapiti project (https://wapiti-scanner.github.io)
# Copyright (C) 2026 Nicolas Surribas
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
from difflib import SequenceMatcher

from wapitiCore.net.response import Response

# Above this similarity ratio, a candidate response is considered a mere copy of
# the server's generic "not found" answer (soft 404 / catch-all page).
SIMILARITY_THRESHOLD = 0.9


def responses_are_similar(response1: str, response2: str) -> bool:
    """Return True when the two response bodies are near-identical."""
    return SequenceMatcher(None, response1, response2).quick_ratio() > SIMILARITY_THRESHOLD


def is_false_positive(response: Response, not_found_response: Response) -> bool:
    """
    Return True when `response` merely replays the generic "not found" answer of the
    server, captured in `not_found_response` by requesting an improbable resource.

    This catches two common setups that would otherwise flood the results:
      - catch-all redirection: any unknown path is redirected to the same location;
      - soft 404 / SPA catch-all: any unknown path returns the same status and a
        near-identical body (e.g. a single-page app shell served for every
        unmatched client-side route).
    """
    # Catch-all redirection: both the improbable path and the candidate are
    # redirected to the very same location.
    if response.redirection_url and not_found_response.redirection_url:
        return response.redirection_url == not_found_response.redirection_url

    # Soft 404: same status code and a near-identical body as the improbable path.
    if not response.redirection_url and not not_found_response.redirection_url:
        return (
            response.status == not_found_response.status
            and responses_are_similar(response.content, not_found_response.content)
        )

    return False
