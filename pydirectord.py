#!/usr/bin/env python3
"""
PyDirectord is a rewrite of 'ldirectord' in python using the twisted framework.
"""
import logging
import optparse
import os

from twisted.internet import reactor

import check
import external
from config import Virtual4, Real4, Fallback4, GlobalConfig
from daemon import Daemon
from enums import *

__author__ = "Martin Herrmann"
__copyright__ = "Copyright 2016, Martin Herrmann"
__credits__ = ["Martin Herrmann"]
__license__ = "GPLv3"
__version__ = "0.9"
__maintainer__ = "Martin Herrmann"
__email__ = "martin.herrmann@tum.de"
__status__ = "Alpha"


def parse_args():
    usage = """%prog [options]

    PyDirectord Copyright (C) 2016 Martin Herrmann
    This program comes with ABSOLUTELY NO WARRANTY.
    This is free software, and you are welcome to redistribute it
    under certain conditions; read LICENSE.txt for details."""

    parser = optparse.OptionParser(usage=usage, version="%prog " + __version__)
    parser.add_option("-d", "--debug", action="store_true", dest="debug", default=False,
                      help="don't start as daemon and log verbosely")
    parser.add_option("-f", "--file", dest="config_file", default=external.config_file,
                      help="use this configuration file [default: %default]", metavar="CONFIG")
    (options, args) = parser.parse_args()

    # parse the config file
    global_config, virtuals = parse_config(options.config_file)

    # make some changes depending on the command-line arguments
    if options.debug:
        global_config.supervised = True
        global_config.log_level = logging.DEBUG

    return global_config, virtuals


def parse_config(configfile):
    # TODO: parse configfile

    #
    # START DEBUG
    #
    virtual = Virtual4(ip="192.168.178.2", port=80, service="http", request="check.php", receive="Running",
                       protocol=Protocol.tcp)
    real1 = Real4(ip="10.150.253.10", port=80, method=ForwardingMethod.gate)
    real2 = Real4(ip="10.150.253.11", port=80, method=ForwardingMethod.gate)
    real3 = Real4(ip="10.150.253.20", port=80, method=ForwardingMethod.gate)
    fallback = Fallback4(ip="127.0.0.1", port=80, method=ForwardingMethod.gate)
    virtual.add_real(real1)
    virtual.add_real(real2)
    virtual.add_real(real3)
    virtual.set_fallback(fallback)

    global_config = GlobalConfig(checkinterval=2, negotiatetimeout=5)
    virtuals = [virtual]
    #
    # STOP DEBUG
    #

    global_config.configfile = configfile
    return global_config, virtuals


def main():
    # parse the command-line arguments
    global_config, virtuals = parse_args()

    # setup Logger
    global_config.log = logging.getLogger("PyDirectord")
    global_config.log.setLevel(global_config.log_level)
    if global_config.supervised:
        handler = logging.StreamHandler()
    else:
        handler = logging.FileHandler(global_config.logfile, 'a', "UTF-8")
    handler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(message)s'))
    global_config.log.addHandler(handler)

    # prepare the check-modules
    check.prepare_check_modules(global_config)

    # perform the final preparations before starting the reactor
    check.initialize(virtuals, global_config)

    if global_config.supervised:
        start_reactor(virtuals, global_config)
    else:
        pidfile = external.pid_path + "pydirectord." + os.path.basename(global_config.configfile) + ".pid"
        global_config.log.info("Daemonizing with pid file " + pidfile)

        pydirectord = PyDirectorDaemon(pidfile, virtuals, global_config)
        pydirectord.start()


def start_reactor(virtuals, global_config):
    # configure cleanup on reactor shutdown
    reactor.addSystemEventTrigger("before", "shutdown", check.cleanup, virtuals, global_config)

    # run the reactor
    reactor.run()

class PyDirectorDaemon(Daemon):
    def __init__(self, pidfile, virtuals, global_config):
        super(PyDirectorDaemon, self).__init__(pidfile)
        self.virtuals = virtuals
        self.global_config = global_config

    def run(self):
        start_reactor(self.virtuals, self.global_config)


if __name__ == '__main__':
    main()
