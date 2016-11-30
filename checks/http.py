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
    timeout = virtual.negotiatetimeout if virtual.negotiatetimeout else global_config.negotiatetimeout

    if virtual.httpmethod == HTTPMethod.GET:
        method = b'GET'
    elif virtual.httpmethod == HTTPMethod.HEAD:
        method = b'HEAD'
    else:
        raise ValueError

    path = (real.request if real.request else virtual.request).encode()
    host = virtual.virtualhost if virtual.virtualhost else real.ip.exploded.encode()

    uri = b'http://' + host + b":" + str(real.port).encode() + b'/' + path

    # prepare deferred
    receive = (real.receive if real.receive else virtual.receive).encode()
    deferred = Deferred()
    deferred.addCallback(__cb_check_body, receive)

    # make request
    agent = Agent(reactor, connectTimeout=timeout)
    d = agent.request(method, uri, None, None)
    d.addCallback(__cb_response, deferred=deferred)
    d.addErrback(__cb_error, deferred=deferred)

    return deferred
