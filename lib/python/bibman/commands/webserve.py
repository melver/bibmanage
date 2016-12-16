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
Webserve command.
"""

import os
import logging
import bottle
import re

from bibman.util import gen_filename_from_bib
from bibman.commands.query import andor_query

DEFAULT_REPONSE_HTML = """<html>
<head>
<title>{{title}}</title>
<style>
body {
  font-family: monospace;
}
</style>
</head>
% for line in lines:
    {{!line}}<br>
% end
</html>"""

@bottle.route("/file/<citekey>/<dlname>")
def index(citekey, dlname):
    query_result = bibfmt.query('citekey', citekey)
    if not query_result:
        return bottle.abort(404, "No such citekey: {}".format(citekey))

    if len(query_result) != 1:
        return bottle.abort(404, "Citekey not unique: {}".format(citekey))

    filepos = query_result[0]

    querydict = bibfmt.read_entry_dict(filepos)
    path = os.path.expanduser(querydict['file'])

    if not os.path.exists(path):
        return bottle.abort(404, "No file found: {}".format(path))

    root = os.path.dirname(path)
    filename = os.path.basename(path)

    return bottle.static_file(filename, root=root)

def process_filepos(filepos):
    querydict = bibfmt.read_entry_dict(filepos)
    raw = bibfmt.read_entry_raw(filepos)
    lines = []

    def re_cite_replace(m):
        links = []
        for ck in m.group(1).split(","):
            ck = ck.strip()
            links.append("<a href=\"/citekey/{citekey}\">{citekey}</a>".format(citekey=ck))
        return "\\cite{{{}}}".format(", ".join(links))

    # FIXME: Modifying URLs into links only works with BibTeX bibliographies
    # right now.
    for line in raw.split("\n"):
        line = line.strip()
        if line.startswith("@"):
            if 'file' in querydict:
                html = bottle.template("<a href=\"/file/{{citekey}}/{{dlname}}\">{{line}}</a>",
                        citekey=querydict['citekey'],
                        dlname=gen_filename_from_bib(querydict), line=line)
            else:
                html = bottle.template("{{line}}", line=line)
        elif line.startswith("file "):
            continue
        elif line == "}":
            html = bottle.template("{{line}}", line=line)
        elif "http" in line:
            html = bottle.template("&nbsp;&nbsp;{{line}}", line=line)
            html = re.sub("(http[^} ]*)([} ]|$)", "<a href=\"\\1\">\\1</a>\\2", html)
        elif "\\cite{" in line:
            html = bottle.template("&nbsp;&nbsp;{{line}}", line=line)
            html = re.sub("\\\\cite{([^}]*)}", re_cite_replace, html)
        else:
            html = bottle.template("&nbsp;&nbsp;{{line}}", line=line)

        lines.append(html)

    return lines

@bottle.route("/citekey/<citekey>")
def index(citekey):
    query_result = bibfmt.query("citekey", citekey)

    if not query_result:
        return bottle.abort(404, "No such citekey: {}".format(citekey))

    if len(query_result) != 1:
        return bottle.abort(404, "Citekey not unique: {}".format(citekey))

    lines = process_filepos(query_result[0])

    return bottle.template(DEFAULT_REPONSE_HTML,
                           title="{} @ {}".format(bibfile.name, citekey),
                           lines=lines)

@bottle.route("/keywords/<keywords>")
def index(keywords):
    query_result = andor_query(bibfmt, "keywords", keywords.split("~"))

    if len(query_result) == 0:
        return bottle.abort(404, "No matching results: {}".format(keywords))

    lines = []
    for filepos in sorted(query_result, reverse=True):
        lines += process_filepos(filepos)

    return bottle.template(DEFAULT_REPONSE_HTML,
                           title="{} @ {}".format(bibfile.name, keywords),
                           lines=lines)

def main(conf):
    global bibfmt_module
    bibfmt_module = conf.bibfmt_module

    try:
        global bibfile
        bibfile = open(conf.args.bibfile, 'r')
    except Exception as e:
        logging.critical("Could not open file: {}".format(e))
        return 1

    try:
        global bibfmt
        bibfmt = bibfmt_module.BibFmt(bibfile)
        bibfmt.build_index('citekey', 'keywords')

        host, port = conf.args.listen.split(":")
        bottle.run(host=host, port=port)
    finally:
        bibfile.close()

def register_args(parser):
    parser.add_argument("-l", "--listen", type=str,
            dest="listen", default="localhost:8080",
            help="Which address and socket to listen on. [Default:localhost:8080]")
    parser.set_defaults(func=main)

