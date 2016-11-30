#!/usr/bin/env python3
"""
PyDirectord is a rewrite of 'ldirectord' in python using the twisted framework.
"""
import logging
import os
from importlib import import_module
from subprocess import CalledProcessError

from twisted.internet import reactor

import external
import ipvsadm
from config import Virtual4, Real4, Fallback4, GlobalConfig
from enums import *

__author__ = "Martin Herrmann"
__copyright__ = "Copyright 2016, Martin Herrmann"
__credits__ = ["Martin Herrmann"]
__license__ = "GPLv3"
__version__ = "0.9"
__maintainer__ = "Martin Herrmann"
__email__ = "martin.herrmann@tum.de"
__status__ = "Alpha"

# this dictionary will eventually contain all check modules
checks = dict()


def cb_running(_, virtual, real, global_config):
    """
    Function called when the outcome of a check-module was positive. Used to update the ipvs table of the kernel if
    necessary.

    :param _: the reason this function is called.
    :param virtual: the virtual service this check was concerned with.
    :param real: the specific real server this check was concerned with.
    :param global_config: the global configuration object.
    :return: nothing
    """
    # determine specific configuration for this service
    virtual_hostname = virtual.ip.exploded + ":" + str(virtual.port)
    real_hostname = real.ip.exploded + ":" + str(real.port)

    global_config.log.debug(real_hostname + "\tOK")

    # reset failure count
    real.failcount = 0

    # check whether the real server is present and has its target weight
    if not real.is_present or real.current_weight < real.weight:
        real.current_weight = real.weight

        global_config.log.info("Setting real " + real_hostname + " to " + str(real.current_weight))
        if real.is_present:
            ipvsadm.edit_real_server(virtual, real, global_config)
        else:
            ipvsadm.add_real_server(virtual, real, global_config)

        # check if the fallback is present
        fallback = virtual.fallback
        if fallback and (fallback.current_weight > 0 or fallback.is_present):
            fallback.current_weight = 0

            # remove it
            if fallback.is_present:
                global_config.log.info("Removing fallback from " + virtual_hostname)
                ipvsadm.delete_real_server(virtual, fallback, global_config)
            else:
                pass  # nothing to do


def cb_error(_, virtual, real, global_config):
    """
    Function called when the outcome of a check-module was negative. Used to update the ipvs table of the kernel if
    necessary.

    :param _: the reason this function is called.
    :param virtual: the virtual service this check was concerned with.
    :param real: the specific real server this check was concerned with.
    :param global_config: the global configuration object.
    :return: nothing
    """
    # determine specific configuration for this service
    failurecount = virtual.failurecount if virtual.failurecount else global_config.failurecount
    quiescent = virtual.quiescent if virtual.quiescent is not None else global_config.quiescent
    readdquiescent = virtual.readdquiescent if virtual.readdquiescent is not None else global_config.readdquiescent
    virtual_hostname = virtual.ip.exploded + ":" + str(virtual.port)
    real_hostname = real.ip.exploded + ":" + str(real.port)

    global_config.log.debug(real_hostname + "\tNOK")

    real.failcount += 1

    # check if we have reached the maximal permitted failure count
    if real.failcount >= failurecount:
        real.failcount = failurecount  # prevent infinite growth of this value

        # just set weight to zero or delete real server altogether depending on quiescent
        if quiescent:
            if real.is_present:
                if real.current_weight == 0:
                    pass  # nothing to do
                else:
                    real.current_weight = 0
                    global_config.log.info("Setting real " + real_hostname + " to " + str(real.current_weight))
                    ipvsadm.edit_real_server(virtual, real, global_config)
            else:
                if readdquiescent:
                    real.current_weight = 0
                    global_config.log.info("Adding real " + real_hostname + " with " + str(real.current_weight)
                                 + " due to readdquiescent")
                    ipvsadm.add_real_server(virtual, real, global_config)
                else:
                    pass  # nothing to do
        else:
            real.current_weight = 0
            if real.is_present:
                global_config.log.info("Removing real " + real_hostname)
                ipvsadm.delete_real_server(virtual, real, global_config)
            else:
                pass  # nothing to do

        # check if there are any real servers left
        for real in virtual.real:
            if real.is_present and real.current_weight > 0:
                return

        # use fallback otherwise
        fallback = virtual.fallback
        if not fallback.is_present or fallback.current_weight < 1:
            fallback.current_weight = 1
            if not fallback.is_present:
                global_config.log.info("Adding fallback for " + virtual_hostname)
                ipvsadm.add_real_server(virtual, fallback, global_config)
            else:
                global_config.log.info("Setting fallback for " + virtual_hostname + " to " + str(fallback.current_weight))
                ipvsadm.edit_real_server(virtual, fallback, global_config)


def cb_repeat(_, virtual, real, global_config):
    """
    Function called whether the outcome of a check-module was positive or negative. Used to reschedule another check in
    the future.

    :param _: the reason this function is called.
    :param virtual: the virtual service this check was concerned with.
    :param real: the specific real server this check was concerned with.
    :param global_config: the global configuration object.
    :return: nothing
    """
    # determine specific configuration for this service
    checkinterval = virtual.checkinterval if virtual.checkinterval else global_config.checkinterval

    # schedule check in the future
    reactor.callLater(checkinterval, do_check, virtual, real, global_config)


def prepare_check_modules(global_config):
    """
    Loads all check-modules present in the correct path.

    :return: nothing
    """
    global_config.log.info("Beginning with check-module loading...")
    for fn in os.listdir(external.check_path):
        if os.path.isfile(external.check_path + fn) and fn != "__init__.py" and fn.endswith(".py"):
            module_name = fn[:-3]
            checks[module_name] = import_module('checks.' + module_name)
            if hasattr(checks[module_name], 'check'):
                global_config.log.info("Check-module '" + module_name + "' has been successfully loaded")
            else:
                global_config.log.error("The module '" + module_name + "' does not seem to be a valid check-module")
                checks[module_name] = None
    global_config.log.info("Check-module loading done")


def initialize_checks(virtuals, global_config):
    # perform the initial setup within ipvsadm
    ipvsadm.initial_ipvs_setup(virtuals, global_config)

    # queue up the check jobs
    for virtual in virtuals:
        for real in virtual.real:
            do_check(virtual, real, global_config)


def cleanup(virtuals, global_config):
    if global_config.cleanstop:
        for virtual in virtuals:
            if virtual.is_present:
                virtual_hostname = virtual.ip.exploded + ":" + str(virtual.port)
                global_config.log.info("Removing virtual service " + virtual_hostname)
                try:
                    ipvsadm.delete_virtual_service(virtual, global_config, sync=True)
                except CalledProcessError:
                    global_config.log.error("Could not remove virtual service " + virtual_hostname)


def do_check(virtual, real, global_config):
    if not checks[virtual.service]:
        global_config.log.error("No check-module found for " + virtual.service)
    else:
        # TODO: currently assumes 'negotiate'
        d = checks[virtual.service].check(virtual, real, global_config)
        d.addCallback(cb_running, virtual, real, global_config)
        d.addErrback(cb_error, virtual, real, global_config)
        d.addBoth(cb_repeat, virtual, real, global_config)


def parse_args():
    usage = """PyDirectord  Copyright (C) 2016  Martin Herrmann
    This program comes with ABSOLUTELY NO WARRANTY.
    This is free software, and you are welcome to redistribute it
    under certain conditions; read LICENSE for details."""  # TODO

    _, config_file = None, None  # optparse.OptionParser(usage)
    return config_file


def parse_config(file):
    # TODO: parse configfile
    virtuals = []
    global_conf = None
    return global_conf, virtuals


def main():
    # parse the command-line arguments
    config_file = parse_args()

    # parse the config file
    global_config, virtuals = parse_config(config_file)

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

    # setup Logger
    global_config.log = logging.getLogger("PyDirectord")
    global_config.log.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(message)s'))
    global_config.log.addHandler(handler)

    # prepare the check-modules
    prepare_check_modules(global_config)

    # perform the final preparations before starting the reactor
    initialize_checks(virtuals, global_config)

    # configure cleanup on reactor shutdown
    reactor.addSystemEventTrigger("before", "shutdown", cleanup, virtuals, global_config)

    # run the reactor
    reactor.run()


if __name__ == '__main__':
    main()
