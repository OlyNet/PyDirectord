#!/usr/bin/env python3
"""
PyDirectord is a rewrite of 'ldirectord' in python using the twisted framework.
"""
import logging
import optparse
import os
import sys

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
    usage = """%prog [options] start | stop | restart | status

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

    # determine initial action
    action = args[0] if len(args) >= 1 else None
    if action is None:
        if global_config.supervised:
            pass  # nothing to do, this is fine
        else:
            print("No action specified, terminating...", file=sys.stderr)
            sys.exit(1)
    elif action == "start":
        global_config.initial_action = Action.start
    elif action == "stop":
        global_config.initial_action = Action.stop
    elif action == "restart":
        global_config.initial_action = Action.restart
    elif action == "reload":
        global_config.initial_action = Action.reload
    elif action == "status":
        global_config.initial_action = Action.status
    else:
        print("Unknown action '%s', terminating..." % action, file=sys.stderr)
        sys.exit(1)

    return global_config, virtuals


def parse_config(configfile):
    # TODO: parse configfile

    #
    # START DEBUG
    #
    virtual1 = Virtual4(ip="192.168.178.2", port=80, service="http", request="check.php", receive="Running",
                       protocol=Protocol.tcp)
    real1 = Real4(ip="10.150.253.10", port=80, method=ForwardingMethod.gate)
    real2 = Real4(ip="10.150.253.11", port=80, method=ForwardingMethod.gate)
    real3 = Real4(ip="10.150.253.20", port=80, method=ForwardingMethod.gate)
    fallback1 = Fallback4(ip="127.0.0.1", port=80, method=ForwardingMethod.gate)
    virtual1.add_real(real1)
    virtual1.add_real(real2)
    virtual1.add_real(real3)
    virtual1.set_fallback(fallback1)

    virtual2 = Virtual4(ip="192.168.178.2", port=443, protocol=Protocol.tcp, checktype=Checktype.connect)
    real4 = Real4(ip="10.150.253.10", port=443, method=ForwardingMethod.gate)
    real5 = Real4(ip="10.150.253.11", port=443, method=ForwardingMethod.gate)
    real6 = Real4(ip="10.150.253.20", port=443, method=ForwardingMethod.gate)
    fallback2 = Fallback4(ip="127.0.0.1", port=443, method=ForwardingMethod.gate)
    virtual2.add_real(real4)
    virtual2.add_real(real5)
    virtual2.add_real(real6)
    virtual2.set_fallback(fallback2)

    global_config = GlobalConfig(checkinterval=2, negotiatetimeout=5)
    virtuals = [virtual1, virtual2]
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

    # check whether to daemonize or not
    if global_config.supervised:
        start_reactor(virtuals, global_config)
    else:
        pidfile = external.pid_path + "pydirectord." + os.path.basename(global_config.configfile) + ".pid"

        pydirectord = PyDirectorDaemon(pidfile, virtuals, global_config)
        if not global_config.initial_action:
            print("No action specified, terminating...", file=sys.stderr)
            sys.exit(1)
        elif global_config.initial_action == Action.start:
            global_config.log.info("Daemonizing with pid file " + pidfile)
            pydirectord.start()
        elif global_config.initial_action == Action.stop:
            pydirectord.stop()
        elif global_config.initial_action == Action.restart:
            pydirectord.restart()
        elif global_config.initial_action == Action.status:
            pydirectord.status()
        elif global_config.initial_action == Action.reload:
            pydirectord.restart()  # FIXME: actually reload instead of restarting
        else:
            raise NotImplementedError("daemon action not yet implemented")

        sys.exit(0)


def start_reactor(virtuals, global_config):
    """
    Does everything necessary before (and including) starting the reactor. This should be the last thing called when
    starting PyDirectord.

    :param virtuals: the list containing all virtual services.
    :param global_config: the global configuration
    :return: nothing
    """
    # prepare the check-modules
    check.prepare_check_modules(global_config)

    # perform the final preparations before starting the reactor
    check.initialize(virtuals, global_config)

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
