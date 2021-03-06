#!/usr/bin/env python3
"""
PyDirectord is a replacement of 'ldirectord' in python using the twisted framework.
"""
import logging
import optparse
import os
import sys
from pathlib import Path

from twisted.internet import reactor
from twisted.logger import globalLogBeginner

import check
import config
import external
from daemon import Daemon
from enums import *

__author__ = "Martin Herrmann"
__copyright__ = "Copyright 2016, Martin Herrmann"
__credits__ = ["Martin Herrmann"]
__license__ = "GPLv3"
__version__ = "0.10"
__maintainer__ = "Martin Herrmann"
__email__ = "martin.herrmann@stormi.io"
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

    config.parse_config(options.config_file)

    # parse the config file
    global_config, virtuals = config.parse_config(options.config_file)

    # insert PyDirectord version information into global_config
    global_config.version = __version__

    # make some changes depending on the command-line arguments
    if options.debug:
        global_config.supervised = True
        global_config.log_level = logging.DEBUG
    else:
        # determine initial action
        action = args[0] if len(args) >= 1 else None
        if action is None:
            if global_config.supervised:
                pass  # nothing to do, this is fine
            else:
                print("No action specified, terminating...", file=sys.stderr)
                sys.exit(4)
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
            sys.exit(4)

    return global_config, virtuals


def check_config_updated(global_config):
    statinfo = os.stat(global_config.configfile)

    # has the config file been modified?
    if statinfo.st_mtime > global_config.last_modified:
        # parse the changed config file
        global_config.new_global_config, global_config.new_virtuals = config.parse_config(global_config.configfile)

        # do a force start just before we terminate
        global_config.action_on_stop = Action.force_start

        # stop reactor and therefore eventually kill the program
        global_config.log.info("The config file '%s' has been updated, restarting..." % global_config.configfile)
        reactor.stop()
    else:
        reactor.callLater(external.config_check_period, check_config_updated, global_config)


def sanity_check(global_config):
    """
    Performs some sanity checks on the environment PyDirectord is run in.

    :param global_config: the global configuration
    :return:
    """
    ipvsadm = Path(external.ipvsadm_path)
    if not ipvsadm.is_file():
        global_config.log.critical("The 'ipvsadm' tool could not be found at %s" % external.ipvsadm_path)
        sys.exit(1)


def main():
    # parse the command-line arguments
    global_config, virtuals = parse_args()

    # redirect the Twisted log to nowhere to prevent a memory 'leak'
    # see: https://twistedmatrix.com/trac/ticket/8164
    globalLogBeginner.beginLoggingTo([lambda _: None], redirectStandardIO=False, discardBuffer=True)

    # setup the actual Logger
    global_config.log = logging.getLogger(__name__)
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
        daemon_handling(virtuals, global_config)


def start_reactor(virtuals, global_config):
    """
    Does everything necessary before (and including) starting the reactor. This should be the last thing called when
    starting PyDirectord.

    :param virtuals: the list containing all virtual services.
    :param global_config: the global configuration
    :return: nothing
    """
    # perform a sanity check of the environment
    sanity_check(global_config)

    # prepare the check-modules
    check.prepare_check_modules(global_config)

    # perform the final preparations before starting the reactor
    check.initialize(virtuals, global_config)

    # configure cleanup on reactor shutdown
    reactor.addSystemEventTrigger("before", "shutdown", check.cleanup, virtuals, global_config)

    # run the reactor
    reactor.run()

    # check if there is something left for us to do
    if global_config.action_on_stop:
        global_config.log.info("'action_on_stop' set to '%s', trying to perform" % global_config.action_on_stop.value)
        daemon_handling(global_config.new_global_config, global_config.new_virtuals)
    else:
        sys.exit(0)


def daemon_handling(virtuals, global_config):
    """
    Handle interactions with the daemon and exit afterwards.

    :param virtuals: the list containing all virtual services.
    :param global_config: the global configuration
    :return: nothing
    """

    pidfile = external.pid_path + "pydirectord." + os.path.basename(global_config.configfile) + ".pid"

    pydirectord = PyDirectorDaemon(pidfile, virtuals, global_config)
    if not global_config.initial_action:
        print("No action specified, terminating...", file=sys.stderr)
        sys.exit(4)
    elif global_config.initial_action == Action.start:
        global_config.log.info("Daemonizing with pid file '%s'" % pidfile)
        pydirectord.start()
    elif global_config.initial_action == Action.stop:
        pydirectord.stop()
    elif global_config.initial_action == Action.restart:
        pydirectord.restart()
    elif global_config.initial_action == Action.status:
        pydirectord.status()
    elif global_config.initial_action == Action.reload:
        pydirectord.restart()  # FIXME: actually reload instead of restarting
    elif global_config.initial_action == Action.force_start:
        pydirectord.force_start()
    else:
        print("Unknown action '%s', terminating..." % global_config.initial_action, file=sys.stderr)
        sys.exit(4)

    sys.exit(0)


class PyDirectorDaemon(Daemon):
    def __init__(self, pidfile, virtuals, global_config):
        super(PyDirectorDaemon, self).__init__(pidfile)
        self.virtuals = virtuals
        self.global_config = global_config

    def run(self):
        start_reactor(self.virtuals, self.global_config)


if __name__ == '__main__':
    # check if we are running as root
    if os.geteuid() != 0:
        print("Must be run as root!", file=sys.stderr)
        sys.exit(1)

    main()
