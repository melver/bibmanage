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
# @file bibman/formats/bibtex.py
# Simple operations on BibTeX file, assuming the format as outlined in
# TEMPLATE_*. Trading off a full parser for speed; for my usecase, this
# implementation is sufficient.
#
# @author Marco Elver <me AT marcoelver.com>
# @date Thu Mar  8 22:34:37 GMT 2012

# TODO: Use proper BibTeX parser for this?

from string import Template
import pprint
import logging

KEYWORDS = "keywords"
FILE     = "file"
HASH     = "md5"
REFNAME  = "refname"

# The '.' after closing '}', is a simple way to enable folding in your
# favorite editor. Folding tags would be '@,}.' .
TEMPLATE_PLAIN = Template("""@${reftype}{${refname},
  author = {${author}},
  title = {${title}},
  year = {${year}},${extra_top}
  keywords = {${keywords}},
  file = {${file}},${extra_bottom}
  annotation = {{${annotation}}},
  date-added = {${date_added}}
}.
""")

TEMPLATE_TOP_ALLOW = ["journal", "number", "pages", "publisher", "volume"]
TEMPLATE_BOTTOM_ALLOW = ["md5"]

def convert_to_dict(entry_string):
    if entry_string[0] != "@": return {}

    try:
        braces = entry_string.index("{")
        comma = entry_string.index(",")

        result = {}
        result["reftype"] = entry_string[1:braces]
        result["refname"] = entry_string[braces+1:comma]

        entry_string = entry_string[comma+1:].strip(". \n{}")
        elements = entry_string.split("},")
        if len(elements) == 1:
            entry_string.split("\",")

        for element in elements:
            key_val = element.split("=")
            if len(key_val) >= 2:
                result[key_val[0].strip()] = key_val[1].strip(" \n{}\"")

        if logging.getLogger().isEnabledFor(logging.DEBUG):
            pp = pprint.PrettyPrinter(indent=4)
            logging.debug("(formats/bibtex:convert_to_dict) result =\n{}".format(
                pp.pformat(result)))

        return result
    except Exception as e:
        logging.error("(formats/bibtex) convert_to_dict(\"\"\"{}\"\"\"): {}".format(
            entry_string, e))
        return {}

class BibFmt:
    def __init__(self, bibfile, template=TEMPLATE_PLAIN):
        self.bibfile = bibfile
        self.index = {}
        self.template = template

    def build_index(self, *toindex):
        # rewind
        self.bibfile.seek(0, 0)

        for index in toindex:
            if self.index.get(index) is None:
                self.index[index] = {}

        valid_entry = False

        # Manually incrementing position and using the line
        # generator of the file object is MUCH faster than 
        # calling readline() ! For purposes of building the index
        # this is sufficient as I will not be seeking in the file.
        line_begin_pos = 0

        for line in self.bibfile:
            line_len = len(line.encode()) # of encoded line, so we can get offset

            if line.startswith("@"):
                valid_entry = True
                last_entry_pos = line_begin_pos

                if REFNAME in toindex:
                    braces = line.index("{")
                    comma = line.index(",")

                    refname = line[braces+1:comma]
                    if self.index[REFNAME].get(refname) is None:
                        self.index[REFNAME][refname] = [last_entry_pos]
                    else:
                        self.index[REFNAME][refname].append(last_entry_pos)
                        logging.warn("Duplicate cite-key found in {}: {}".format(
                            self.bibfile.name, refname))

            elif line == "}.\n" or line == "}\n":
                valid_entry = False

            # now strip it
            line = line.strip()

            if valid_entry:
                if KEYWORDS in toindex:
                    if line.startswith(KEYWORDS):
                        # This will not work for multi-line keywords. Tradeoff
                        # between proper parser and speed.
                        keywords = line.split("=")[1].strip(" ,{}").split(",")
                        for keyword in keywords:
                            if self.index[KEYWORDS].get(keyword) is None:
                                self.index[KEYWORDS][keyword] = [last_entry_pos]
                            else:
                                self.index[KEYWORDS][keyword].append(last_entry_pos)

                if FILE in toindex:
                    if line.startswith(FILE):
                        filename = line.split("=")[1].strip(" ,{}")
                        self.index[FILE][filename] = last_entry_pos

                if HASH in toindex:
                    if line.startswith(HASH):
                        filename = line.split("=")[1].strip(" ,{}")
                        self.index[HASH][filename] = last_entry_pos

            line_begin_pos += line_len

    def query(self, index, key):
        try:
            return self.index[index][key]
        except:
            return None

    def read_entry_raw(self, filepos):
        self.bibfile.seek(filepos, 0)
        result = []

        while True:
            line = self.bibfile.readline()
            if len(line) == 0: break

            result.append(line)

            if line == "}.\n" or line == "}\n":
                break

        return "".join(result)

    def read_entry_dict(self, filepos):
        self.bibfile.seek(filepos, 0)
        entry_lines = []

        while True:
            line = self.bibfile.readline()
            if len(line) == 0: break

            entry_lines.append(line.strip())

            if line == "}.\n" or line == "}\n": break

        return convert_to_dict("".join(entry_lines))

    def _process_extra(self, kwargs):
        # Add optional top information
        extra_top_strings = []

        for item in TEMPLATE_TOP_ALLOW:
            if item in kwargs:
                extra_top_strings.append("\n  {} = {{{}}},".format(
                    item.replace("_", "-"), kwargs[item]))

        kwargs["extra_top"] = "".join(extra_top_strings)

        # Add bottom information
        extra_bottom_strings = []

        # pad file entry, so future file moves can be facilitated
        file_padding = 128 - len(kwargs["file"])
        if file_padding > 0:
            extra_bottom_strings.append("".ljust(file_padding))

        for item in TEMPLATE_BOTTOM_ALLOW:
            if item in kwargs:
                extra_bottom_strings.append("\n  {} = {{{}}},".format(
                    item.replace("_", "-"), kwargs[item]))

        kwargs["extra_bottom"] = "".join(extra_bottom_strings)
        return kwargs

    def print_new_entry(self, **kwargs):
        print(self.template.safe_substitute(**self._process_extra(kwargs)))

    def append_new_entry(self, **kwargs):
        # seek to end
        self.bibfile.seek(0, 2)
        self.bibfile.write(self.template.safe_substitute(**self._process_extra(kwargs)))
        self.bibfile.write("\n")

    def update_in_place(self, filepos, key, old_val, value):
        self.bibfile.seek(filepos, 0)

        while True:
            start_line_pos = self.bibfile.tell()
            line = self.bibfile.readline()
            if len(line) == 0: break
            if line == "}.\n" or line == "}\n": break

            strip_line = line.strip()
            if key == FILE:
                if strip_line.startswith(key):
                    new_line = line.rstrip().replace(old_val, value,
                            1).ljust(len(line)-1) + "\n"

                    if len(line) != len(new_line):
                        return False

                    self.bibfile.seek(start_line_pos, 0)
                    self.bibfile.write(new_line)
                    break

        return True

