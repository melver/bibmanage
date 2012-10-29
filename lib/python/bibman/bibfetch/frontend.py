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
# @file bibman/bibfetch/frontend.py
# TODO: Add description here.
#
# @author Marco Elver <me AT marcoelver.com>
# @date Fri Mar  9 20:47:50 GMT 2012

import subprocess
import os
import re
import logging
import pprint

class Frontend:
    def __init__(self, args):
        self.backends = []
        for backend in args.fetch_prio_list:
            self.backends.append(getattr(__import__("bibman.bibfetch.{}".format(backend),
                    fromlist=["remote_fetch"]), "remote_fetch"))

    def extract_fileinfo(self, kwargs):
        if "filename" in kwargs:
            if kwargs["filename"].split(".")[-1].lower() == "pdf":
                pdftext = subprocess.Popen(["pdftotext", "-q",
                    os.path.expanduser(kwargs["filename"]), "-"],
                    stdout=subprocess.PIPE).communicate()[0]
                pdftext = re.sub(b'\W', b' ', pdftext).decode()
                words = pdftext.strip().split()[:20]

                kwargs["textsearch"] = " ".join(words)

        return kwargs

    def __call__(self, **kwargs):
        """
        @return Dictionary with keys as in format modules (see format.bibtex
                for an example). Missing entries will be added automatically.
        """

        kwargs = self.extract_fileinfo(kwargs)

        if logging.getLogger().isEnabledFor(logging.DEBUG):
            pp = pprint.PrettyPrinter(indent=4)
            logging.debug("(bibfetch/frontend:Frontend) __call__::kwargs =\n{}".format(
                pp.pformat(kwargs)))

        for backend in self.backends:
            result = backend(**kwargs)
            if result is not None:
                return result

