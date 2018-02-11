from twisted.internet import reactor
from twisted.internet._sslverify import optionsForClientTLS
from twisted.internet.defer import Deferred
from twisted.web.client import Agent, readBody, BrowserLikePolicyForHTTPS, _requireSSL
from twisted.web.http_headers import Headers

from pydexceptions import UnexpectedResultException
from enums import *


class CheckContextFactory(BrowserLikePolicyForHTTPS):
    def __init__(self, hostname=None, trustRoot=None):
        super(CheckContextFactory, self).__init__(trustRoot=trustRoot)
        self._hostname = hostname.encode()

    @_requireSSL
    def creatorForNetloc(self, hostname, port):
        if self._hostname is not None:
            act_hostname = self._hostname
        else:
            act_hostname = hostname
        return optionsForClientTLS(act_hostname.decode("ascii"), trustRoot=self._trustRoot)


def __cb_check_body(body, receive):
    if body != receive:
        raise UnexpectedResultException("got '" + str(body) + "' expected '" + str(receive) + "'")


def __cb_received_body(body, deferred):
    deferred.callback(body)


def __cb_error(reason, deferred):
    deferred.errback(reason)


def __cb_response(response, deferred):
    d = readBody(response)
    d.addCallback(__cb_received_body, deferred=deferred)


def check(virtual, real, global_config):
    # setup parameters
    if virtual.httpmethod == HTTPMethod.GET:
        method = b'GET'
    elif virtual.httpmethod == HTTPMethod.HEAD:
        method = b'HEAD'
    else:
        raise ValueError

    hostname = virtual.hostname if virtual.hostname else real.ip.exploded
    port = str(virtual.checkport if virtual.checkport else real.port)
    path = real.request if real.request else virtual.request

    uri = b'https://' + real.ip.exploded.encode() + b":" + port.encode() + b'/' + path.encode()

    # prepare headers
    headers = {'User-Agent': ['PyDirectord ' + global_config.version], 'Host': [hostname]}

    # prepare ssl
    contextFactory = CheckContextFactory(hostname=hostname)

    # prepare deferred
    receive = (real.receive if real.receive else virtual.receive).encode()
    deferred = Deferred()
    deferred.addCallback(__cb_check_body, receive)

    # make request
    agent = Agent(reactor, contextFactory=contextFactory, connectTimeout=virtual.negotiatetimeout)
    d = agent.request(method, uri, Headers(headers), None)
    d.addCallback(__cb_response, deferred=deferred)
    d.addErrback(__cb_error, deferred=deferred)

    return deferred
