from twisted.internet import protocol
from twisted.internet import reactor
from twisted.internet.defer import Deferred
from twisted.mail import imap4


class _IMAP4CheckClient(imap4.IMAP4Client):
    """
    A client with callbacks for greeting messages from an IMAP server.
    """
    deferred = None

    def serverGreeting(self, caps):
        self.factory.greetingReceived()
        self.logout()
        if caps is not None:
            self.deferred.callback(self)
        else:
            self.deferred.errback("capabilities is empty")


class _IMAP4CheckFactory(protocol.ClientFactory):
    usedUp = False

    protocol = _IMAP4CheckClient

    def __init__(self, deferred, timeout):
        self.deferred = deferred
        self.timeout = timeout
        self.greeting_received = False

    def buildProtocol(self, addr):
        assert not self.usedUp
        self.usedUp = True

        self.p = self.protocol()
        self.p.factory = self
        self.p.deferred = self.deferred
        self.p.setTimeout(self.timeout)

        return self.p

    def greetingReceived(self):
        """
        To be called by the protocol instance if it has received a greeting
        so clientConnectionLost will not trigger the errback.
        """
        self.greeting_received = True

    def clientConnectionFailed(self, connector, reason):
        self.deferred.errback(reason)

    def clientConnectionLost(self, connector, reason):
        if not self.greeting_received:
            self.deferred.errback(reason)


def check(virtual, real, global_config):
    port = virtual.checkport if virtual.checkport else real.port

    deferred = Deferred()

    factory = _IMAP4CheckFactory(deferred, virtual.negotiatetimeout)
    reactor.connectTCP(real.ip.exploded.encode(), port, factory, timeout=virtual.negotiatetimeout)

    return deferred
