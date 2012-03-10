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
# @file bibman/bibfetch/gscholar.py
#   ** Based on: https://github.com/venthur/gscholar **
#
# @author Marco Elver <me AT marcoelver.com>
# @date Fri Mar  9 20:47:50 GMT 2012

import urllib.request, urllib.error, urllib.parse
import re
import hashlib
import random
import logging
from html.entities import name2codepoint

from bibman.formats import bibtex as bibtex_format

# fake google id (looks like it is a 16 elements hex)
google_id = hashlib.md5(str(random.random()).encode()).hexdigest()[:16] 

GOOGLE_SCHOLAR_URL = "http://scholar.google.com"
# the cookie looks normally like: 
#        'Cookie' : 'GSP=ID=%s:CF=4' % google_id }
# where CF is the format (e.g. bibtex). since we don't know the format yet, we
# have to append it later
HEADERS = {'User-Agent' : 'Mozilla/5.0',
        'Cookie' : 'GSP=ID={}'.format(google_id) }

# These are defined by Gscholar
FORMAT_BIBTEX = 4
FORMAT_ENDNOTE = 3
FORMAT_REFMAN = 2
FORMAT_WENXIANWANG = 5

def query(searchstr):
    """Return a list of bibtex items."""
    logging.debug("Query: {}".format(searchstr))
    searchstr = '/scholar?q='+urllib.parse.quote(searchstr)
    url = GOOGLE_SCHOLAR_URL + searchstr
    header = HEADERS
    header['Cookie'] = header['Cookie'] + ":CF={}".format(FORMAT_BIBTEX)
    request = urllib.request.Request(url, headers=header)
    response = urllib.request.urlopen(request)
    html = response.read().decode()

    result = []

    # - grab the links
    # - follow the bibtex links to get the bibtex entries
    for link in get_links(html):
        url = GOOGLE_SCHOLAR_URL+link
        request = urllib.request.Request(url, headers=header)
        response = urllib.request.urlopen(request)
        bib = response.read().decode()
        result.append(bib)

    return result

def get_links(html):
    """Return a list of reference links from the html."""
    refre = re.compile(r'<a href="(/scholar\.bib\?[^>]*)">')
    reflist = refre.findall(html)

    # escape html enteties
    reflist = (re.sub('&({});'.format('|'.join(name2codepoint)), lambda m:
        chr(name2codepoint[m.group(1)]), s) for s in reflist)

    return reflist


def remote_fetch(**kwargs):
    if "textsearch" in kwargs:
        result = query(kwargs["textsearch"])
        for i in range(len(result)):
            print("===== RESULT [{}]: =====".format(i+1))
            print(result[i])
            print()
        try:
            choice = int(input("Which result? Number [Default: 1]: ")) - 1
            if choice < 0 or choice >= len(result):
                raise
        except:
            choice = 0

        print()

        return bibtex_format.convert_to_dict(result[choice])
    else:
        return {}
