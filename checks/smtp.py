from twisted.internet import reactor
from twisted.internet.defer import Deferred
from twisted.internet.error import ConnectionDone
from twisted.internet.protocol import ClientFactory, connectionDone
from twisted.mail._except import SMTPConnectError, SMTPProtocolError, SMTPTimeoutError, SMTPClientError
from twisted.mail.smtp import DNSNAME, SUCCESS
from twisted.protocols import basic
from twisted.protocols.policies import TimeoutMixin


class _SMTPConnectProtocol(basic.LineReceiver, TimeoutMixin):
    timeout = None

    def __init__(self, identity, log=None):
        if isinstance(identity, str):
            identity = identity.encode('ascii')

        self.identity = identity or b''
        self.resp = []
        self.code = -1
        self.log = log

    def sendLine(self, line):
        basic.LineReceiver.sendLine(self, line)

    def connectionMade(self):
        if self.log:
            self.log.debug("Connection to server made")

        self.setTimeout(self.timeout)

        self._expected = [220]
        self._okresponse = self.smtpState_helo
        self._failresponse = self.smtpConnectionFailed

    def connectionLost(self, reason=connectionDone):
        """
        We are no longer connected
        """
        self.setTimeout(None)

    def timeoutConnection(self):
        if self.log:
            self.log.debug("Timeout waiting for SMTP server response")

        self.sendError(SMTPTimeoutError(-1, b"Timeout waiting for SMTP server response"))

    def lineReceived(self, line):
        if self.log:
            self.log.debug("Line received: " + str(line))

        self.resetTimeout()

        why = None

        try:
            self.code = int(line[:3])
        except ValueError:
            # This is a fatal error and will disconnect the transport
            # lineReceived will not be called again.
            if self.log:
                self.log.debug("Invalid response from SMTP server: {}".format(line))

            self.sendError(SMTPProtocolError(-1, "Invalid response from SMTP server: {}".format(line)))
            return

        if line[0:1] == b'0':
            # Verbose informational message, ignore it
            return

        self.resp.append(line[4:])

        if line[3:4] == b'-':
            # Continuation
            return

        if self.code in self._expected:
            why = self._okresponse(self.code, b'\n'.join(self.resp))
        else:
            why = self._failresponse(self.code, b'\n'.join(self.resp))

        self.code = -1
        self.resp = []
        return why

    def smtpConnectionFailed(self, code, resp):
        self.sendError(SMTPConnectError(code, resp))

    def smtpState_helo(self, code, resp):
        if self.log:
            self.log.debug("Sending 'HELO'")

        self.sendLine(b'HELO ' + self.identity)
        self._expected = SUCCESS
        self._okresponse = self._disconnectFromServer

    def smtpState_disconnect(self, code, resp):
        self.transport.loseConnection()

        if code in SUCCESS:
            self.factory.result.callback(code)
        else:
            self.factory.result.errback(code)

    def sendError(self, exc):
        """
        If an error occurs before a mail message is sent sendError will be
        called.  This base class method sends a QUIT if the error is
        non-fatal and disconnects the connection.

        @param exc: The SMTPClientError (or child class) raised
        @type exc: C{SMTPClientError}
        """
        if self.log:
            self.log.debug("Got SMTPClientError:" + str(exc))

        if isinstance(exc, SMTPClientError) and not exc.isFatal:
            self._disconnectFromServer()
        else:
            # If the error was fatal then the communication channel with the
            # SMTP Server is broken so just close the transport connection
            self.smtpState_disconnect(-1, None)

    def _disconnectFromServer(self, code, resp):
        if self.log:
            self.log.debug("Sending 'QUIT'")

        self._expected = range(0, 1000)
        self._okresponse = self.smtpState_disconnect
        self.sendLine(b'QUIT')


class _SMTPConnectFactory(ClientFactory):
    domain = DNSNAME
    protocol = _SMTPConnectProtocol

    def __init__(self, deferred, timeout=None, log=None):
        """
        @param deferred: A Deferred to callback or errback when sending
        of this message completes.
        @type deferred: L{defer.Deferred}

        @param timeout: Period, in seconds, for which to wait for
        server responses, or None to wait forever.
        """

        self.result = deferred
        self.result.addBoth(self._removeDeferred)
        self.sendFinished = False
        self.currentProtocol = None
        self.log = log
        self.timeout = timeout

    def _removeDeferred(self, result):
        del self.result
        return result

    def clientConnectionFailed(self, connector, err):
        self._processConnectionError(connector, err)

    def clientConnectionLost(self, connector, err):
        self._processConnectionError(connector, err)

    def _processConnectionError(self, connector, err):
        if err.check(ConnectionDone):
            err.value = SMTPConnectError(-1, "Unable to connect to server.")

        self.currentProtocol = None
        self.result.errback(err.value)

    def buildProtocol(self, addr):
        p = self.protocol(self.domain, log=self.log)
        p.factory = self
        p.timeout = self.timeout
        self.currentProtocol = p
        self.result.addBoth(self._removeProtocol)
        return p

    def _removeProtocol(self, result):
        """
        Remove the protocol created in C{buildProtocol}.

        @param result: The result/error passed to the callback/errback of
            L{defer.Deferred}.

        @return: The C{result} untouched.
        """
        if self.currentProtocol:
            self.currentProtocol = None
        return result


def check(virtual, real, global_config):
    deferred = Deferred()
    senderFactory = _SMTPConnectFactory(deferred, timeout=virtual.negotiatetimeout)
    reactor.connectTCP(real.ip.exploded.encode(), real.port, senderFactory)
    return deferred
