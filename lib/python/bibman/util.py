#!/usr/bin/env python

#
# Copyright (C) 2012, Marco Elver <me AT marcoelver.com>
#
# This file is part of Bibman.
#
# Bibman is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Bibman is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Bibman.  If not, see <http://www.gnu.org/licenses/>.
#

##
# @file bibman/util.py
# TODO: Add description here.
#
# @author Marco Elver <me AT marcoelver.com>
# @date Fri Mar  9 19:32:58 GMT 2012

import hashlib
import string

FILENAME_VALID_CHARS = frozenset("-_(). {}{}".format(string.ascii_letters, string.digits))

def gen_hash_md5(path):
    md5 = hashlib.md5()

    with open(path, "rb") as f:
        f.seek(0, 2)
        fsize = f.tell()
        f.seek(0, 0)

        while f.tell() != fsize:
            md5.update(f.read(128))

    return md5

def gen_filename_from_bib(bibdict):
    # If the title has a : in it, I assume it's in the TITLE:MOREDESCRIPTIVETITLE format.
    # We can exploit this to get a shorter filename.
    title = bibdict["title"][:35].split(":")[0].replace(" ", "_")

    filename = "".join(
            [bibdict["refname"],
            "-",
            title,
            ".",
            bibdict["file"].split(".")[-1] # extension
        ])

    return ''.join(c for c in filename if c in FILENAME_VALID_CHARS)

