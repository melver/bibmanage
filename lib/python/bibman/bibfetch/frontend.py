# Copyright (c) 2012-2016, Marco Elver <me AT marcoelver.com>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Bibfetch frontent, calling all backends until one succeeds.
"""

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

