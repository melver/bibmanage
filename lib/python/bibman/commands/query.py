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

import bibman.formats.bibtex as bibtex_format

AVAIL_INDICES = [bibtex_format.KEYWORDS]

def main(args):
    if not args.index in AVAIL_INDICES:
        logging.critical("Not a valid choice: {}".format(args.index))
        return 1

    try:
        bibfile = open(args.bibfile, 'r')
    except Exception as e:
        logging.critical("Could not open file: {}".format(e))
        return 1

    try:
        bibfmt = bibtex_format.BibFmt(bibfile)
        bibfmt.build_index(args.index)

        if args.index == bibtex_format.KEYWORDS:
            # Perform query
            query_result = set()
            for value_or in " ".join(args.value).split("+"):
                last_result = None
                for value_and in value_or.split(","):
                    this_result = bibfmt.query(args.index, value_and) or []
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
                    if args.copy is not None:
                        if not os.path.isdir(args.copy):
                            logging.critical("Not a valid path: {}".format(args.copy))
                            return 1

                        querydict = bibfmt.read_entry_dict(filepos)
                        filepath = querydict["file"]

                        if args.rename:
                            newname = "".join([querydict["refname"],
                                "__",
                                querydict["title"][:30].replace(" ", "_").split(":")[0],
                                ".",
                                filepath.split(".")[-1] # extension
                                ])
                            destpath = os.path.join(args.copy, newname)
                        else:
                            destpath = args.copy

                        logging.info("Copying: '{}' to '{}'".format(filepath, destpath))
                        shutil.copy(os.path.expanduser(filepath), destpath)
                    else:
                        print(bibfmt.read_entry_raw(filepos))
    finally:
        bibfile.close()

def register_args(parser):
    parser.add_argument("-i", "--index", type=str,
            dest="index", required=True,
            help="Index to query. [Availble:{}]".format(
                ",".join(AVAIL_INDICES)))
    parser.add_argument(type=str,
            dest="value", nargs="+",
            help="Query value. 'Or' semantics with '+', 'and' semantics with ','.")
    parser.add_argument("-c", "--copy", metavar="PATH", type=str,
            dest="copy", default=None,
            help="Copy associated files to PATH.")
    parser.add_argument("--rename", action="store_true",
            dest="rename", default=False,
            help="Only valid with --copy: rename file to be more descriptive.")
    parser.set_defaults(func=main)

