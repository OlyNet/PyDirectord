import os
from importlib import import_module

from twisted.internet import reactor

from config import Virtual4, Real4
from enums import *

check_path = '/home/martin/git/pydirectord/checks/'

checks = dict()


def cb_running(_, virtual, real):
    print(real.ip.exploded + ":" + str(real.port) + "\tOK")
    # TODO: handle real online


def cb_error(_, virtual, real):
    print(real.ip.exploded + ":" + str(real.port) + "\tNOK")
    # TODO: handle real offline


def cb_repeat(_, virtual, real):
    checkinterval = virtual.checkinterval if virtual.checkinterval else 2  # TODO: take from global config
    reactor.callLater(checkinterval, do_check, virtual, real)


def prepare_check_modules():
    for fn in os.listdir(check_path):
        if os.path.isfile(check_path + fn) and fn != "__init__.py" and fn.endswith(".py"):
            module_name = fn[:-3]
            checks[module_name] = import_module('checks.' + module_name)
            if hasattr(checks[module_name], 'check'):
                print("Check module '" + module_name + "' has been successfully imported.")
            else:
                print("The module '" + module_name + "' does not seem to be a valid check module.")


def initialize_checks(virtuals):
    for virtual in virtuals:
        for real in virtual.real:
            do_check(virtual, real)


def do_check(virtual, real):
    d = checks[virtual.service].check(virtual, real)
    d.addCallback(cb_running, virtual, real)
    d.addErrback(cb_error, virtual, real)
    d.addBoth(cb_repeat, virtual, real)


def parse_args(args):
    # TODO: parse commandline arguments
    pass


def parse_config(file):
    # TODO: parse configfile
    virtuals = []
    global_conf = None
    return global_conf, virtuals


def main():
    prepare_check_modules()

    virtual = Virtual4(ip="129.187.43.210", port=80, service="http", request="check.php", receive="Running",
                       protocol=Protocol.tcp)
    real1 = Real4(ip="10.150.253.10", port=80, method=ForwardingMethod.gate)
    real2 = Real4(ip="10.150.253.11", port=80, method=ForwardingMethod.gate)
    real3 = Real4(ip="10.150.253.20", port=80, method=ForwardingMethod.gate)
    virtual.add_real(real1)
    virtual.add_real(real2)
    virtual.add_real(real3)

    initialize_checks([virtual])

    reactor.run()


if __name__ == '__main__':
    main()
