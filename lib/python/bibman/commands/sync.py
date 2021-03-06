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
Sync command.
"""

import logging
import os
import datetime
import shutil
import string

from bibman.util import gen_hash_md5, gen_filename_from_bib

class SyncCommand:
    def __init__(self, conf, bibfile, excludefiles):
        self.conf = conf
        self.bibfmt_main = bibfmt_module.BibFmt(bibfile)

        indices = [bibfmt_module.FILE, bibfmt_module.CITEKEY]
        if self.conf.args.hash:
            indices.append(bibfmt_module.HASH)

        self.bibfmt_main.build_index(*indices)

        self.bibfmt_efs = []
        for fh in excludefiles:
            bi = bibfmt_module.BibFmt(fh)
            bi.build_index(*indices)
            self.bibfmt_efs.append(bi)

        # Sanity check data and warn
        for idx in indices:
            main_set = frozenset(self.bibfmt_main.index[idx])
            for bi in self.bibfmt_efs:
                duplicate_set = set(bi.index[idx])
                duplicate_set &= main_set

                if len(duplicate_set) != 0:
                    logging.warning("Duplicates found in '{}': {} = {}".format(
                        bi.bibfile.name, idx, duplicate_set))

    def walk_path(self):
        for path in self.conf.args.paths:
            if not os.path.isdir(path):
                logging.error("Could not find directory: {}".format(path))
                continue

            for root, dirs, files in os.walk(path):
                for f in files:
                    fullpath = os.path.abspath(os.path.join(root, f))
                    if fullpath.startswith(os.environ['HOME']):
                        fullpath = fullpath.replace(os.environ['HOME'], "~", 1)

                    if fullpath.split(".")[-1] in self.conf.args.extlist:
                        yield fullpath

    def query_exists_in(self, index, value):
        """
        Generates all found matches.
        """
        for bi in [self.bibfmt_main] + self.bibfmt_efs:
            if value in bi.index[index]:
                yield bi

    def query_exists(self, *args, **kwargs):
        """
        Returns first found match only.
        """
        for bi in self.query_exists_in(*args, **kwargs):
            return bi
        return None

    def check_hash(self, digest, path):
        found = False

        for bi in self.query_exists_in(bibfmt_module.HASH, digest):
            found = True

            query_filepos = bi.query(bibfmt_module.HASH, digest)
            query_result = bi.read_entry_dict(query_filepos)
            duplicate = query_result["file"]
            citekey = query_result["citekey"]

            if not os.path.exists(duplicate) and bi.bibfile.writable():
                if not self.conf.args.append or not bi.update_in_place(query_filepos,
                        bibfmt_module.FILE, duplicate, path):
                    logging.warning("File '{}' missing; suggested fix: update '{}' in '{}' with '{}'".format(
                        duplicate, citekey, bi.bibfile.name, path))
                else:
                    # Could update in-place
                    logging.info("Updated entry for '{}' with '{}'".format(
                        citekey, path))
            else:
                logging.warning("Duplicate for '{}' found in '{}': citekey = '{}'".format(
                    path, bi.bibfile.name, citekey))

        return found

    def verify_hash(self, path):
        # Only verify entries in main.
        query_filepos = self.bibfmt_main.query(bibfmt_module.FILE, path)
        if query_filepos is None: return  # not in main
        query_result = self.bibfmt_main.read_entry_dict(query_filepos)
        digest = gen_hash_md5(os.path.expanduser(path)).hexdigest()
        if digest != query_result["md5"]:
            logging.warn("MD5 checksum mismatch: {} ({} != {})".format(
                path, digest, query_result["md5"]))

    def interactive_corrections(self, new_entry_args):
        logging.info("Entering interactive corrections mode. Leave blank for default.")
        self.bibfmt_main.print_new_entry(**new_entry_args)

        for key in new_entry_args:
            if key in ["file", "date_added", "md5"]:
                continue

            user_data = input("'{}' correction: ".format(key))
            if len(user_data) > 0:
                new_entry_args[key] = user_data

        print()

        return new_entry_args

    def __call__(self):
        for path in self.walk_path():
            # Check existing entries
            if self.query_exists(bibfmt_module.FILE, path) is not None:
                if self.conf.args.verify: self.verify_hash(path)
                continue

            # Generate new entry
            new_entry_args = dict(
                    reftype="misc",
                    citekey="TODO:{}".format(os.path.basename(path)),
                    author="",
                    title="",
                    year="",
                    keywords="",
                    file=path,
                    annotation="",
                    date_added=datetime.date.today().strftime("%Y-%m-%d"))

            if self.conf.args.hash:
                new_entry_args["md5"] = gen_hash_md5(
                        os.path.expanduser(path)).hexdigest()

                # Before we proceed, check if this file is a duplicate of an
                # already existing file, and if so, check existing entry is
                # still valid; if not valid replace file, otherwise warn user.
                if self.check_hash(new_entry_args["md5"], path):
                    continue

            if self.conf.args.remote:
                logging.info("Attempting to fetch bibliography information remotely: {}".format(
                    path))
                new_entry_args.update(self.conf.bibfetch(filename=path))

            if self.conf.args.interactive:
                new_entry_args = self.interactive_corrections(new_entry_args)

            if self.conf.args.interactive and self.conf.args.rename:
                newpath = os.path.join(os.path.dirname(path), gen_filename_from_bib(new_entry_args))
                logging.info("Rename: {} to {}".format(path, newpath))
                shutil.move(os.path.expanduser(path), os.path.expanduser(newpath))
                new_entry_args["file"] = newpath
                path = newpath

            # Before we add the new entry, check for duplicate cite-keys
            citekey_exists_in = self.query_exists(bibfmt_module.CITEKEY,
                                                  new_entry_args["citekey"])
            if citekey_exists_in is not None:
                logging.debug("Cite-key already exists in '{}': {}".format(
                    citekey_exists_in.bibfile.name, new_entry_args["citekey"]))

                for c in string.ascii_letters:
                    newcitekey = new_entry_args["citekey"] + c
                    if self.query_exists(bibfmt_module.CITEKEY, newcitekey) is None:
                        break
                new_entry_args["citekey"] = newcitekey

            # Finally, generate new entry

            if self.conf.args.append:
                logging.info("Appending new entry for: {}".format(path))
                self.bibfmt_main.append_new_entry(**new_entry_args)
            else:
                self.bibfmt_main.print_new_entry(**new_entry_args)

def main(conf):
    global bibfmt_module
    bibfmt_module = conf.bibfmt_module

    try:
        bibfile = open(conf.args.bibfile, 'r+')

        excludefiles = []
        if conf.args.excludes is not None:
            for filename in conf.args.excludes:
                excludefiles.append(open(filename, "r"))
    except Exception as e:
        logging.critical("Could not open file: {}".format(e))
        return 1

    try:
        sync_cmd = SyncCommand(conf, bibfile, excludefiles)
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
            help="Bibliography files to exclude new entries from.")
    parser.add_argument("--nohash", action="store_false",
            dest="hash", default=True,
            help="Do not generate MD5 sums and check duplicates.")
    parser.add_argument("-i", "--interactive", action="store_true",
            dest="interactive", default=False,
            help="Interactive synchronisation, prompting the user for entry corrections.")
    parser.add_argument("--remote", action="store_true",
            dest="remote", default=False,
            help="Enable remote fetching of bibliography entries.")
    parser.add_argument("--rename", action="store_true",
            dest="rename", default=False,
            help="Rename file to be more descriptive; only valid with --interactive.")
    parser.add_argument("--verify", action="store_true",
            dest="verify", default=False,
            help="Verify checksum of all existing entries.")
    parser.set_defaults(func=main)

