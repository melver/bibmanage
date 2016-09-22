#!/usr/bin/env python
#
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
Bibliography manager main file.
"""

import sys
import argparse
import time
import logging

from bibman.bibfetch import frontend as bibfetch_frontend
from bibman.commands import sync, query, webserve

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
                            dest="fetch_prio_list", default=[], nargs="+",
                            help="Priority list of fetching engines to use.")
        parser.add_argument("-b", "--bibfile", metavar="BIBFILE", type=str,
                            dest="bibfile", required=True,
                            help="Bibliograpy file to work with.")

        # Add subparsers
        subparsers = parser.add_subparsers(
                title="Commands",
                description="Available commands to manage bibliography files.",
                help="Summary")

        parser_sync = subparsers.add_parser("sync", aliases=["s"],
                help="Synchronise bibliography file with path.")
        sync.register_args(parser_sync)

        parser_query = subparsers.add_parser("query", aliases=["q"],
                help="Query bibliography file.")
        query.register_args(parser_query)

        parser_webserve = subparsers.add_parser("webserve", aliases=["w"],
                help="Webserver for bibliography file.")
        webserve.register_args(parser_webserve)

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

