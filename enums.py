from enum import Enum


class ForwardingMethod(Enum):
    gate = 0
    masq = 1
    ipip = 2


class Scheduler(Enum):
    """
    See: http://manpages.ubuntu.com/manpages/trusty/man8/ipvsadm.8.html
    """
    rr = 0
    wrr = 1
    lc = 2
    wlc = 3
    lblc = 4
    lblcr = 5
    dh = 6
    sh = 7
    sed = 8
    nq = 9


class ServerStatus(Enum):
    starting = 0
    running = 1
    stopping = 2
    reloading = 3
    all = 255


class Service(Enum):
    ftp = 21
    smtp = 25
    dns = 53
    http = 80
    pop = 110
    nntp = 119
    imap = 143
    ldap = 389
    https = 443
    submission = 587
    ldaps = 636  # newly added
    imaps = 993
    pops = 995
    oracle = 1521
    radius = 1812
    http_proxy = 3128
    mysql = 3306
    pgsql = 5432
    sip = 5060


class Checktype(Enum):
    connect = 0
    external = 1
    external_perl = 2  # deprecated
    negotiate = 3
    off = 4
    on = 5
    ping = 6
    negotiate_connect = 7


class HTTPMethod(Enum):
    GET = 0
    HEAD = 1


class Protocol(Enum):
    tcp = 0
    udp = 1
    fwm = 3
