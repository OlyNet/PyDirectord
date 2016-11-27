from twisted.internet import reactor

from checks import http
from config import Virtual4, Real4
from enums import *


def cb_running(_, virtual, real):
    print(real.ip.exploded + ":" + str(real.port) + "\tOK")
    # TODO: handle real online


def cb_error(_, virtual, real):
    print(real.ip.exploded + ":" + str(real.port) + "\tNOK")
    # TODO: handle real offline


def cb_repeat(_, virtual, real):
    checkinterval = virtual.checkinterval if virtual.checkinterval else 2  # TODO: take from global config
    reactor.callLater(checkinterval, do_check, virtual, real)


def initialize_checks(virtuals):
    for virtual in virtuals:
        for real in virtual.real:
            do_check(virtual, real)


def do_check(virtual, real):
    # TODO: automatically figure out which check to run
    d = http.check(virtual, real)
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
    virtual = Virtual4(ip="129.187.43.210", port=80, service=Service.http, request="check.php", receive="Running",
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
