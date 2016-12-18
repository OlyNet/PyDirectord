import sys

from twisted.internet import reactor
from twisted.internet.endpoints import TCP4ClientEndpoint, TCP6ClientEndpoint
from twisted.internet.protocol import Protocol, Factory

from structures import Virtual4, Virtual6


class _DummyProtocol(Protocol):
    pass


class _DummyFactory(Factory):
    def buildProtocol(self, _):
        return _DummyProtocol()


def __cb_connection_established(protocol):
    protocol.transport.loseConnection()


def check(virtual, real, global_config):
    port = virtual.checkport if virtual.checkport else real.port

    if isinstance(virtual, Virtual4):
        point = TCP4ClientEndpoint(reactor, real.ip.exploded, port, timeout=virtual.checktimeout)
    elif isinstance(virtual, Virtual6):
        point = TCP6ClientEndpoint(reactor, real.ip.exploded, port, timeout=virtual.checktimeout)
    else:
        global_config.log.critical("Not a valid Virtual4/Virtual6 service. This should not happen!")
        sys.exit(1)

    d = point.connect(_DummyFactory())
    d.addCallback(__cb_connection_established)
    return d
