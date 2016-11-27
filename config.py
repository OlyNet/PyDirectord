import ipaddress

from pyparsing import basestring

from enums import *


class General(object):
    """
    This contains the general configuration options that apply to all virtual servers or the whole process.
    """

    def __init__(self, checktimeout=5, negotiatetimeout=30, checkinterval=10, failurecount=1, autoreload=False,
                 callback=None, fallback=None, fallbackcommand=None, logfile="/var/log/pydirectord.log",
                 emailalert=None, emailalertfrom=None, emailalertfreq=0, emailalertstatus=ServerStatus.all,
                 smtp=None, execute=None, supervised=False, quiescent=True, readdquiescent=True, cleanstop=True,
                 maintenancedir=None):
        # TODO
        pass


class __Virtual(object):
    """
    Base-class for virtual server configuration.
    """

    def __init__(self, port, checktimeout=None, negotiatetimeout=None, checkinterval=None, cleanstop=None,
                 checktype=Checktype.negotiate, emailalert=None, emailalertfrom=None, quiescent=None, service=None,
                 checkcommand=None, checkport=None, request=None, receive=None, httpmethod=HTTPMethod.GET,
                 virtualhost=None, login=None, passwd=None, database=None, secret=None, scheduler=Scheduler.wrr,
                 persistent=None, netmask=None, protocol=None):
        self.ip = None

        if isinstance(port, int) and 0 < port <= 65535:
            self.port = port
        else:
            raise ValueError

        if isinstance(checktimeout, int) and checktimeout > 0:
            self.checktimeout = checktimeout
        elif checktimeout is None:
            self.checktimeout = None
        else:
            raise ValueError

        if isinstance(negotiatetimeout, int) and negotiatetimeout > 0:
            self.negotiatetimeout = negotiatetimeout
        elif negotiatetimeout is None:
            self.negotiatetimeout = None
        else:
            raise ValueError

        if isinstance(checkinterval, int) and checkinterval > 0:
            self.checkinterval = checkinterval
        elif checkinterval is None:
            self.checkinterval = None
        else:
            raise ValueError

        if isinstance(checktype, Checktype):
            self.checktype = checktype
        else:
            raise ValueError

        if isinstance(quiescent, bool):
            self.quiescent = quiescent
        elif quiescent is None:
            self.quiescent = None
        else:
            raise ValueError

        if isinstance(service, basestring):
            self.service = service
        elif service is None:
            self.service = None
        else:
            raise ValueError

        if isinstance(checkport, int) and 0 < checkport <= 65535:
            self.checkport = checkport
        elif checkport is None:
            self.checkport = port
        else:
            raise ValueError

        if isinstance(request, basestring):
            self.request = request
        elif request is None:
            self.request = None
        else:
            raise ValueError

        if isinstance(receive, basestring):
            self.receive = receive
        elif receive is None:
            self.receive = None
        else:
            raise ValueError

        if isinstance(virtualhost, basestring):
            self.virtualhost = virtualhost
        elif virtualhost is None:
            self.virtualhost = None
        else:
            raise ValueError

        if isinstance(protocol, Protocol):
            self.protocol = protocol
        else:
            raise ValueError

        if isinstance(scheduler, Scheduler):
            self.scheduler = scheduler
        else:
            raise ValueError

        if isinstance(httpmethod, HTTPMethod):
            self.httpmethod = httpmethod
        else:
            raise ValueError


class Virtual4(__Virtual):
    """
    Configuration of a IPv4 virtual server.
    """

    def __init__(self, ip, **kwargs):
        super(Virtual4, self).__init__(**kwargs)

        # check for valid IPv4
        self.ip = ipaddress.ip_address(ip)
        if self.ip.version != 4:
            raise ValueError

        # variable initialization
        self.fallback = None
        self.real = []

    def add_real(self, real):
        if isinstance(real, Real4):
            self.real.append(real)
        else:
            raise ValueError

    def remove_real(self, real):
        self.real.remove(real)

    def set_fallback(self, fallback=None):
        if isinstance(fallback, Fallback4):
            self.fallback = fallback
        elif fallback is None:
            self.fallback = None
        else:
            raise ValueError


class __Real(object):
    """
    Base-class for real server configuration
    """

    def __init__(self, port, method, weight=1, request=None, receive=None):
        self.ip = None

        if isinstance(port, int) and 0 < port <= 65535:
            self.port = port
        else:
            raise ValueError

        if isinstance(method, ForwardingMethod):
            self.method = method
        else:
            raise ValueError

        if isinstance(weight, int) and weight >= 0:
            self.weight = weight
        else:
            raise ValueError

        if isinstance(request, basestring):
            self.request = request
        elif request is None:
            self.request = None
        else:
            raise ValueError

        if isinstance(receive, basestring):
            self.receive = receive
        elif receive is None:
            self.receive = None
        else:
            raise ValueError

        # variable initialization
        self.failcount = 0


class Real4(__Real):
    """
    Configuration of an IPv4 real server.
    """

    def __init__(self, ip, **kwargs):
        super(Real4, self).__init__(**kwargs)

        # check for valid IPv4
        self.ip = ipaddress.ip_address(ip)
        if self.ip.version != 4:
            raise ValueError


class __Fallback(object):
    """
    Base-class for fallback server configuration
    """
    pass


class Fallback4(__Fallback):
    """
    Configuration of an IPv4 fallback server.
    """

    def __init__(self, ip, port):
        # check for valid IPv4
        self.ip = ipaddress.ip_address(ip)
        if self.ip.version != 4:
            raise ValueError

        # check for valid port
        if isinstance(self.port, int) and 0 > port <= 65535:
            self.port = port
        else:
            raise ValueError
