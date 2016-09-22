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
Query command.
"""

import sys
import os
import logging
import shutil

from bibman.util import gen_filename_from_bib

def andor_query(bibfmt, index, values, andsep=','):
    query_result = set()

    for value_or in values:
        last_result = None
        for value_and in value_or.split(andsep):
            this_result = bibfmt.query(index, value_and) or []
            if last_result is None:
                last_result = set(this_result)
            else:
                last_result &= frozenset(this_result)
        query_result |= last_result

    return query_result

def main(conf):
    bibfmt_module = conf.bibfmt_module
    AVAIL_INDICES = [bibfmt_module.KEYWORDS, bibfmt_module.CITEKEY]

    if not conf.args.index in AVAIL_INDICES:
        logging.critical("Not a valid choice: {}. Available options are: {}".format(
                         conf.args.index, ",".join(AVAIL_INDICES)))
        return 1

    try:
        bibfile = open(conf.args.bibfile, 'r')
    except Exception as e:
        logging.critical("Could not open file: {}".format(e))
        return 1

    try:
        bibfmt = bibfmt_module.BibFmt(bibfile)
        bibfmt.build_index(conf.args.index)

        if conf.args.value[0] != "-":
            values = (x for x in conf.args.value)
        else:
            values = (x.strip() for x in sys.stdin)

        # Perform query
        query_result = andor_query(bibfmt, conf.args.index, values)

        # Show results
        if len(query_result) == 0:
            logging.info("No matches.")
        else:
            for filepos in sorted(query_result):
                if conf.args.copy is not None:
                    if not os.path.isdir(conf.args.copy):
                        logging.critical("Not a valid path: {}".format(conf.args.copy))
                        return 1

                    querydict = bibfmt.read_entry_dict(filepos)
                    filepath = querydict["file"]

                    if conf.args.rename:
                        destpath = os.path.join(conf.args.copy,
                                gen_filename_from_bib(querydict))
                    else:
                        destpath = conf.args.copy

                    logging.info("Copying: '{}' to '{}'".format(filepath, destpath))
                    shutil.copy(os.path.expanduser(filepath), destpath)
                else:
                    print(bibfmt.read_entry_raw(filepos))
    finally:
        bibfile.close()

def register_args(parser):
    parser.add_argument("-i", "--index", type=str,
            dest="index", default="citekey",
            help="Index to query. [Default:citekey]")
    parser.add_argument(type=str,
            dest="value", nargs="+",
            help="Query value; 'or' semantics for multiple arguments, 'and' semantics with ',' within one argument.")
    parser.add_argument("-c", "--copy", metavar="PATH", type=str,
            dest="copy", default=None,
            help="Copy associated files to PATH.")
    parser.add_argument("--rename", action="store_true",
            dest="rename", default=False,
            help="Only valid with --copy: rename file to be more descriptive.")
    parser.set_defaults(func=main)

