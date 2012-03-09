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
# @file bibman/main.py
# Bibliography manager main file.
#
# @author Marco Elver <me AT marcoelver.com>
# @date Mon Feb  6 18:28:43 GMT 2012

import sys
import argparse
import time
import logging

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
        parser.add_argument("-b", "--bibfile", metavar="BIBFILE", type=str,
                dest="bibfile", required=True,
                help="BibTeX file to work with.")

        # Add subparsers
        subparsers = parser.add_subparsers(
                title="Commands",
                description="Available commands to manage BibTeX files.",
                help="Summary"
                )

        parser_sync = subparsers.add_parser("sync", aliases=["s"],
                help="Synchronise BibTeX file with path.")
        sync.register_args(parser_sync)

        parser_query = subparsers.add_parser("query", aliases=["q"],
                help="Query BibTeX file.")
        query.register_args(parser_query)

        # Parse args and setup logging
        self.args = parser.parse_args()
        self._setup_logging()

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
    bibman_config = BibmanConfig()

    # Run the command
    result = bibman_config.args.func(bibman_config.args)

    logging.info("All done in {:.2f} sec!".format(time.time() - the_time))
    return result

if __name__ == "__main__":
    sys.exit(main(sys.argv))

