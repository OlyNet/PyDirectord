from twisted.conch import error
from twisted.conch.ssh import transport
from twisted.internet import defer, protocol, reactor
from twisted.internet.defer import Deferred

from pydexceptions import UnexpectedResultException


class _SSHCheckClient(transport.SSHClientTransport):
    def verifyHostKey(self, pubKey, fingerprint):
        if self.fingerprint is not None and fingerprint != self.fingerprint:
            self.stateGood = False
            self.failure_reason = "fingerprint mismatch (received %s)" % fingerprint
            return defer.fail(error.ConchError('bad key'))
        else:
            self.stateGood = True
            return defer.succeed(1)

    def connectionSecure(self):
        self.stateGood = True
        self.loseConnection()


class _SSHCheckClientFactory(protocol.ClientFactory):
    protocol = _SSHCheckClient

    def __init__(self, deferred, fingerprint=None):
        self.deferred = deferred
        self.fingerprint = fingerprint

    def buildProtocol(self, addr):
        self.p = self.protocol()
        self.p.factory = self
        self.p.fingerprint = self.fingerprint
        self.p.stateGood = False
        return self.p

    def clientConnectionFailed(self, connector, reason):
        self.deferred.errback(reason)

    def clientConnectionLost(self, connector, reason):
        if self.p.stateGood:
            self.deferred.callback("ok")
        else:
            self.deferred.errback(UnexpectedResultException(self.p.failure_reason if self.p.failure_reason else reason))


def check(virtual, real, global_config):
    port = virtual.checkport if virtual.checkport else real.port

    deferred = Deferred()

    factory = _SSHCheckClientFactory(deferred, fingerprint=virtual.fingerprint.encode())
    reactor.connectTCP(virtual.ip.exploded.encode(), port, factory, timeout=virtual.negotiatetimeout)

    return deferred
