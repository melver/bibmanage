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

from string import Template

KEYWORDS = "keywords"
FILE     = "file"
HASH     = "md5"

# The '.' after closing '}', is a simple way to enable folding in your
# favorite editor. Folding tags would be '@,}.' .
TEMPLATE_PLAIN = Template("""@${reftype}{${refname},
  author = {${author}},
  title = {${title}},
  year = {${year}},
  keywords = {${keywords}},
  file = {${file}},${extra}
  annotation = {{}},
  date-added = {${date_added}}
}.
""")

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
            line_len = len(line)

            if line.startswith("@"):
                valid_entry = True
                last_entry_pos = line_begin_pos
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
        result = {}
        while True:
            line = self.bibfile.readline()
            if len(line) == 0: break
            if line == "}.\n" or line == "}\n": break

            line = line.strip()
            if line.startswith("@"):
                tmp = line.split("{")
                result["reftype"] = tmp[0].lstrip("@")
                result["refname"] = tmp[1].rstrip(", \n")
            elif line.startswith("author"):
                result["author"] = line.split("=")[1].strip("{}, ")
            elif line.startswith("title"):
                result["title"] = line.split("=")[1].strip("{}, ")
            elif line.startswith("year"):
                result["year"] = line.split("=")[1].strip("{}, ")
            elif line.startswith("keywords"):
                result["keywords"] = line.split("=")[1].strip("{}, ").split(",")
            elif line.startswith("file"):
                result["file"] = line.split("=")[1].strip("{}, ")
            elif line.startswith("date-added"):
                result["date_added"] = line.split("=")[1].strip("{}, ")
            elif line.startswith("md5"):
                result["md5"] = line.split("=")[1].strip("{}, ")

        return result

    def _process_extra(self, kwargs):
        extra_strings = []

        # pad file entry, so future file moves can be facilitated
        file_padding = 128 - len(kwargs["file"])
        if file_padding > 0:
            extra_strings.append("".ljust(file_padding))

        if "md5" in kwargs:
            extra_strings.append("\n  md5 = {{{}}},".format(kwargs["md5"]))
            del kwargs["md5"]

        kwargs["extra"] = "".join(extra_strings)
        return kwargs

    def print_new_entry(self, **kwargs):
        print(self.template.substitute(**self._process_extra(kwargs)))

    def append_new_entry(self, **kwargs):
        # seek to end
        self.bibfile.seek(0, 2)
        self.bibfile.write(self.template.substitute(**self._process_extra(kwargs)))
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

