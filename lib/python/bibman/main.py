#!/usr/bin/env python

#
# Copyright (C) 2012-2013, Marco Elver <me AT marcoelver.com>
#
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
#

##
# @file bibman/main.py
# Bibliography manager main file.
#
# @author Marco Elver <me AT marcoelver.com>

import sys
import argparse
import time
import logging

from bibman.bibfetch import frontend as bibfetch_frontend
from bibman.commands import sync, query

class BibmanConfig:
    """
    Configuration class which maintains the global configuration of the program.
    """
    def __init__(self):
        # Global args
        parser = argparse.ArgumentParser(prog="bibman",
                description="Bibliography manager.")
        parser.add_argument("--loglevel", metavar="LEVEL", type=str,
                dest="loglevel", default="INFO",
                help="Loglevel (DEBUG, INFO, WARNING, ERROR, CRITICAL). [Default:INFO]")
        parser.add_argument("--format", metavar="FORMAT", type=str,
                dest="format", default="bibtex",
                help="Bibliography format. [Default:bibtex]")
        parser.add_argument("--fetch-prio", metavar="PRIOLIST", type=str,
                dest="fetch_prio_list", default=["gscholar"], nargs="+",
                help="Priority list of fetching engines to use.")
        parser.add_argument("-b", "--bibfile", metavar="BIBFILE", type=str,
                dest="bibfile", required=True,
                help="Bibliograpy file to work with.")

        # Add subparsers
        subparsers = parser.add_subparsers(
                title="Commands",
                description="Available commands to manage bibliography files.",
                help="Summary"
                )

        parser_sync = subparsers.add_parser("sync", aliases=["s"],
                help="Synchronise bibliography file with path.")
        sync.register_args(parser_sync)

        parser_query = subparsers.add_parser("query", aliases=["q"],
                help="Query bibliography file.")
        query.register_args(parser_query)

        # Parse args and setup logging
        self.args = parser.parse_args()
        self._setup_logging()

        # Get the format module
        self.bibfmt_module = __import__("bibman.formats.{}".format(self.args.format),
                fromlist=["*"])

        # Setup the remote fetching engine
        self.bibfetch = bibfetch_frontend.Frontend(self.args)

    def _setup_logging(self):
        """
        Sets up the logging interface.
        All modules wishing to log messages, should import the logging module
        and use the given interface. logging.getLogger() returns the default logger,
        which is the one being set up in this function.
        """
        try:
            loglevel = getattr(logging, self.args.loglevel.upper())
        except AttributeError:
            loglevel = logging.INFO

        logging.basicConfig(level=loglevel,format='[Bibman:%(levelname)s] %(message)s')

def main(argv):
    # Initialize
    the_time = time.time()

    try:
        bibman_config = BibmanConfig()
    except ImportError as e:
        logging.critical("{}".format(e))
        return 1

    # Run the command
    result = bibman_config.args.func(bibman_config)

    logging.info("All done in {:.2f} sec!".format(time.time() - the_time))
    return result

if __name__ == "__main__":
    sys.exit(main(sys.argv))

