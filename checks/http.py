from twisted.internet import reactor
from twisted.internet.defer import Deferred
from twisted.web.client import Agent, readBody

from UnexpectedResult import UnexpectedResult
from enums import *


def __cb_check_body(body, receive):
    if body != receive:
        raise UnexpectedResult("got '" + body + "' expected '" + receive + "'")


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

    host = (virtual.hostname if virtual.hostname else real.ip.exploded).encode()
    port = str((virtual.checkport if virtual.checkport else real.port)).encode()
    path = (real.request if real.request else virtual.request).encode()

    uri = b'http://' + host + b":" + port + b'/' + path

    # prepare deferred
    receive = (real.receive if real.receive else virtual.receive).encode()
    deferred = Deferred()
    deferred.addCallback(__cb_check_body, receive)

    # make request
    agent = Agent(reactor, connectTimeout=virtual.negotiatetimeout)
    d = agent.request(method, uri, None, None)
    d.addCallback(__cb_response, deferred=deferred)
    d.addErrback(__cb_error, deferred=deferred)

    return deferred
