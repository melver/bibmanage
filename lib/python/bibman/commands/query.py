#!/usr/bin/env python

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

##
# @file bibman/commands/query.py
# TODO: Add description here.
#
# @author Marco Elver <me AT marcoelver.com>
# @date Thu Mar  8 19:05:57 GMT 2012

import logging
import os
import shutil

from bibman.util import gen_filename

def main(conf):
    bibfmt_module = conf.bibfmt_module
    AVAIL_INDICES = [bibfmt_module.KEYWORDS]

    if not conf.args.index in AVAIL_INDICES:
        logging.critical("Not a valid choice: {}. Available options are: {}".format(conf.args.index,
            ",".join(AVAIL_INDICES)))
        return 1

    try:
        bibfile = open(conf.args.bibfile, 'r')
    except Exception as e:
        logging.critical("Could not open file: {}".format(e))
        return 1

    try:
        bibfmt = bibfmt_module.BibFmt(bibfile)
        bibfmt.build_index(conf.args.index)

        if conf.args.index == bibfmt_module.KEYWORDS:
            # Perform query
            query_result = set()
            for value_or in conf.args.value:
                last_result = None
                for value_and in value_or.split(","):
                    this_result = bibfmt.query(conf.args.index, value_and) or []
                    if last_result is None:
                        last_result = set(this_result)
                    else:
                        last_result &= frozenset(this_result)
                query_result |= last_result

            # Show results
            if len(query_result) == 0:
                logging.info("No matches.")
            else:
                for filepos in query_result:
                    if conf.args.copy is not None:
                        if not os.path.isdir(conf.args.copy):
                            logging.critical("Not a valid path: {}".format(conf.args.copy))
                            return 1

                        querydict = bibfmt.read_entry_dict(filepos)
                        filepath = querydict["file"]

                        if conf.args.rename:
                            destpath = os.path.join(conf.args.copy,
                                    gen_filename(querydict))
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
            dest="index", default="keywords",
            help="Index to query. [Default:keywords]")
    parser.add_argument(type=str,
            dest="value", nargs="+",
            help="Query value. 'Or' semantics for space separated arguments, 'and' semantics with ',' within one argument.")
    parser.add_argument("-c", "--copy", metavar="PATH", type=str,
            dest="copy", default=None,
            help="Copy associated files to PATH.")
    parser.add_argument("--rename", action="store_true",
            dest="rename", default=False,
            help="Only valid with --copy: rename file to be more descriptive.")
    parser.set_defaults(func=main)

