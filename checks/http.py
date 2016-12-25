from twisted.internet import reactor
from twisted.internet.defer import Deferred
from twisted.web.client import Agent, readBody
from twisted.web.http_headers import Headers

from UnexpectedResult import UnexpectedResult
from enums import *


def __cb_check_body(body, receive):
    if body != receive:
        raise UnexpectedResult("got '" + str(body) + "' expected '" + str(receive) + "'")


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

    uri = b'http://' + real.ip.exploded.encode() + b":" + port.encode() + b'/' + path.encode()

    # prepare headers
    headers = {'User-Agent': ['Pydirectord 0.9'], 'Host': [hostname]}

    # prepare deferred
    receive = (real.receive if real.receive else virtual.receive).encode()
    deferred = Deferred()
    deferred.addCallback(__cb_check_body, receive)

    # make request
    agent = Agent(reactor, connectTimeout=virtual.negotiatetimeout)
    d = agent.request(method, uri, Headers(headers), None)
    d.addCallback(__cb_response, deferred=deferred)
    d.addErrback(__cb_error, deferred=deferred)

    return deferred
