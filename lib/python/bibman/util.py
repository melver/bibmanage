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
Utility functions
"""

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
            [bibdict["citekey"],
            "-",
            title,
            ".",
            bibdict["file"].split(".")[-1] # extension
        ])

    return ''.join(c for c in filename if c in FILENAME_VALID_CHARS)

