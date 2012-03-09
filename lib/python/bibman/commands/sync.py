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
# @file bibman/commands/sync.py
# TODO: Add description here.
#
# @author Marco Elver <me AT marcoelver.com>
# @date Thu Mar  8 19:05:57 GMT 2012

import logging
import os
import datetime
import hashlib

import bibman.formats.bibtex as bibtex_format

class SyncCommand:
    def __init__(self, args, bibfile, excludefiles):
        self.args = args
        self.bibfmt_main = bibtex_format.BibFmt(bibfile)

        indices = [bibtex_format.FILE]
        if self.args.hash:
            indices.append(bibtex_format.HASH)

        self.bibfmt_main.build_index(*indices)

        self.bibfmt_efs = []
        for fh in excludefiles:
            bi = bibtex_format.BibFmt(fh)
            bi.build_index(*indices)
            self.bibfmt_efs.append(bi)

    def walk_path(self):
        for path in self.args.paths:
            if not os.path.isdir(path):
                logging.error("Could not find directory: {}".format(path))
                continue

            for root, dirs, files in os.walk(path):
                for f in files:
                    fullpath = os.path.abspath(os.path.join(root,f))
                    if fullpath.startswith(os.environ['HOME']):
                        fullpath = fullpath.replace(os.environ['HOME'], "~", 1)

                    if fullpath.split(".")[-1] in self.args.extlist:
                        yield fullpath

    def __call__(self):
        for path in self.walk_path():
            # Check existing entries
            found = False
            for bi in [self.bibfmt_main] + self.bibfmt_efs:
                if path in bi.index[bibtex_format.FILE]:
                    found = True
                    break
            if found: continue

            # Generate new entry

            new_entry_args = dict(
                    reftype="misc",
                    refname="TODO:{}".format(os.path.basename(path)),
                    author="",
                    title="",
                    year="",
                    keywords="",
                    file=path,
                    date_added=datetime.date.today().strftime("%Y-%m-%d"))

            if self.args.hash:
                md5 = hashlib.md5()
                with open(os.path.expanduser(path), "rb") as f:
                    f.seek(0, 2)
                    fsize = f.tell()
                    f.seek(0, 0)

                    while f.tell() != fsize:
                        md5.update(f.read(128))
                new_entry_args["md5"] = md5.hexdigest()

                # Before we proceed, check if this file is a duplicate of an
                # already existing file, and if so, check existing entry is
                # still valid; if not valid replace file otherwise, warn user.
                found = False
                for bi in [self.bibfmt_main] + self.bibfmt_efs:
                    if new_entry_args["md5"] in bi.index[bibtex_format.HASH]:
                        found = True
                        query_result = bi.query(bibtex_format.HASH, new_entry_args["md5"])
                        duplicate = bi.read_entry_dict(query_result)["file"]
                        refname = bi.read_entry_dict(query_result)["refname"]

                        logging.warn("Duplicate for '{}' found in: '{}', refname: '{}'".format(
                            path, bi.bibfile.name, refname
                            ))

                        if not os.path.exists(duplicate) and bi.bibfile.writable():
                            if not self.args.append or not bi.update_in_place(query_result,
                                    bibtex_format.FILE, duplicate, path):
                                logging.warn("File '{}' does not exist anymore, suggested fix: update entry '{}' in '{}' with '{}'.\n".format(
                                    duplicate, refname, bi.bibfile.name, path))
                            else:
                                # Could update in-place
                                logging.info("Updated entry for '{}'.".format(
                                            refname))

                # Do not write
                if found: continue

            # Finally, generate new entry

            if self.args.append:
                logging.info("Appending new entry for: {}".format(path))
                self.bibfmt_main.append_new_entry(**new_entry_args)
            else:
                self.bibfmt_main.print_new_entry(**new_entry_args)

def main(args):
    try:
        bibfile = open(args.bibfile, 'r+')

        excludefiles = []
        if args.excludes is not None:
            for filename in args.excludes:
                excludefiles.append(open(filename, "r"))
    except Exception as e:
        logging.critical("Could not open file: {}".format(e))
        return 1

    try:
        sync_cmd = SyncCommand(args, bibfile, excludefiles)
        sync_cmd()
    finally:
        bibfile.close()
        for fh in excludefiles:
            fh.close()

def register_args(parser):
    parser.add_argument("-p", "--path", metavar="PATH", type=str,
            dest="paths", nargs="+", required=True,
            help="Paths to scan and synchronise BIBFILE with.")
    parser.add_argument("--extlist", type=str,
            dest="extlist", default="pdf", nargs="+",
            help="File-extensions to consider for sync. [Default:pdf]")
    parser.add_argument("-a", "--append", action='store_true',
            dest="append", default=False,
            help="Append to BIBFILE instead of printing to stdout.")
    parser.add_argument("-e", "--exclude", metavar="EXCLUDE", type=str,
            dest="excludes", default=None, nargs="+",
            help="BibTeX files to exclude new entries from.")
    parser.add_argument("--nohash", action="store_false",
            dest="hash", default=True,
            help="Do not generate MD5 sums and check duplicates.")
    parser.set_defaults(func=main)

