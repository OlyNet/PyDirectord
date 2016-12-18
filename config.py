import configparser
import json
import sys

from enums import *
from structures import Fallback4, Real4, Virtual4, GlobalConfig


def __illegal_config_value(section, key, value, allowed):
    print("Illegal configuration value '%s' for %s in section '%s'. Allowed values are: %s"
          % (value, key, section, allowed), file=sys.stderr)
    sys.exit(1)


def __parse_host(hoststring):
    tmp1 = hoststring.rsplit(" ", 1)
    tmp2 = tmp1[0].rsplit(":", 1)

    host = tmp2[0]
    port = int(tmp2[1])
    if tmp1[1] == "gate":
        method = ForwardingMethod.gate
    elif tmp1[1] == "masq":
        method = ForwardingMethod.masq
    elif tmp1[1] == "ipip":
        method = ForwardingMethod.ipip
    else:
        raise ValueError

    return host, port, method


def parse_config(file):
    config = configparser.ConfigParser()
    config.read(file)

    global_config = None
    virtuals = list()
    sections = config.sections()

    for section in sections:
        # special 'global' section handling
        if section == "global":
            global_args = dict()
            global_args["configfile"] = file
            for key in config[section]:
                if key == "autoreload":
                    try:
                        global_args["autoreload"] = cur_section.getboolean(key)
                    except ValueError:
                        __illegal_config_value(section, key, cur_section[key],
                                               "'yes'/'no', 'on'/'off', 'true'/'false' and '1'/'0'")
                elif key == "supervised":
                    try:
                        global_args["supervised"] = cur_section.getboolean(key)
                    except ValueError:
                        __illegal_config_value(section, key, cur_section[key],
                                               "'yes'/'no', 'on'/'off', 'true'/'false' and '1'/'0'")
                elif key == "smtp":
                    global_args["smtp"] = cur_section[key]  # FIXME
                elif key == "logfile":
                    global_args["logfile"] = cur_section[key]
                elif key == "callback":
                    global_args["callback"] = cur_section[key]
                elif key == "maintenancedir":
                    global_args["maintenancedir"] = cur_section[key]
                elif key == "configfile":
                    global_args["configfile"] = cur_section[key]
            global_config = GlobalConfig(**global_args)
        else:
            virtual_args = dict()
            virtual_args["description"] = section
            reals = list()
            fallback = None
            cur_section = config[section]
            for key in config[section]:
                if key == "real":
                    for hoststring in json.loads(cur_section[key]):
                        ip, port, method = __parse_host(hoststring)
                        real = Real4(ip=ip, port=port, method=method)
                        reals.append(real)
                elif key == "fallback":
                    ip, port, method = __parse_host(cur_section[key])
                    fallback = Fallback4(ip=ip, port=port, method=method)
                elif key == "host":
                    virtual_args["ip"] = cur_section[key]  # TODO: handle hostnames
                elif key == "port":
                    try:
                        virtual_args["port"] = int(cur_section[key])
                        if not 0 < virtual_args["port"] <= 65535:
                            __illegal_config_value(section, key, cur_section[key], "0 < port <= 65535")
                    except ValueError:
                        __illegal_config_value(section, key, cur_section[key], "0 < port <= 65535")
                elif key == "checkport":
                    try:
                        virtual_args["checkport"] = int(cur_section[key])
                        if not 0 < virtual_args["checkport"] <= 65535:
                            __illegal_config_value(section, key, cur_section[key], "0 < checkport <= 65535")
                    except ValueError:
                        __illegal_config_value(section, key, cur_section[key], "0 < checkport <= 65535")
                elif key == "checktimeout":
                    try:
                        virtual_args["checktimeout"] = int(cur_section[key])
                        if not 0 < virtual_args["checktimeout"]:
                            __illegal_config_value(section, key, cur_section[key], "0 < checktimeout")
                    except ValueError:
                        __illegal_config_value(section, key, cur_section[key], "0 < checktimeout")
                elif key == "negotiatetimeout":
                    try:
                        virtual_args["negotiatetimeout"] = int(cur_section[key])
                        if not 0 < virtual_args["negotiatetimeout"]:
                            __illegal_config_value(section, key, cur_section[key], "0 < negotiatetimeout")
                    except ValueError:
                        __illegal_config_value(section, key, cur_section[key], "0 < negotiatetimeout")
                elif key == "checkinterval":
                    try:
                        virtual_args["checkinterval"] = int(cur_section[key])
                        if not 0 < virtual_args["checkinterval"]:
                            __illegal_config_value(section, key, cur_section[key], "0 < checkinterval")
                    except ValueError:
                        __illegal_config_value(section, key, cur_section[key], "0 < checkinterval")
                elif key == "failurecount":
                    try:
                        virtual_args["failurecount"] = int(cur_section[key])
                        if not 0 <= virtual_args["failurecount"]:
                            __illegal_config_value(section, key, cur_section[key], "0 <= failurecount")
                    except ValueError:
                        __illegal_config_value(section, key, cur_section[key], "0 <= failurecount")
                elif key == "cleanstop":
                    try:
                        virtual_args["cleanstop"] = cur_section.getboolean("cleanstop")
                    except ValueError:
                        __illegal_config_value(section, key, cur_section[key],
                                               "'yes'/'no', 'on'/'off', 'true'/'false' and '1'/'0'")
                elif key == "quiescent":
                    try:
                        virtual_args["quiescent"] = cur_section.getboolean("quiescent")
                    except ValueError:
                        __illegal_config_value(section, key, cur_section[key],
                                               "'yes'/'no', 'on'/'off', 'true'/'false' and '1'/'0'")
                elif key == "readdquiescent":
                    try:
                        virtual_args["readdquiescent"] = cur_section.getboolean("readdquiescent")
                    except ValueError:
                        __illegal_config_value(section, key, cur_section[key],
                                               "'yes'/'no', 'on'/'off', 'true'/'false' and '1'/'0'")
                elif key == "persistent":
                    try:
                        virtual_args["persistent"] = int(cur_section[key])
                        if not 0 < virtual_args["persistent"]:
                            __illegal_config_value(section, key, cur_section[key], "0 < persistent")
                    except ValueError:
                        __illegal_config_value(section, key, cur_section[key], "0 < persistent")
                elif key == "protocol":
                    raw = cur_section[key]
                    if raw == "tcp":
                        virtual_args["protocol"] = Protocol.tcp
                    elif raw == "udp":
                        virtual_args["protocol"] = Protocol.udp
                    elif raw == "fwm":
                        virtual_args["protocol"] = Protocol.fwm
                    else:
                        __illegal_config_value(section, key, cur_section[key], "tcp, udp, fwm")
                elif key == "checktype":
                    raw = cur_section[key]
                    if raw == "connect":
                        virtual_args["checktype"] = Checktype.connect
                    elif raw == "external" or raw == "external-perl":
                        virtual_args["checktype"] = Checktype.external
                    elif raw == "negotiate":
                        virtual_args["checktype"] = Checktype.negotiate
                    elif raw == "off":
                        virtual_args["checktype"] = Checktype.off
                    elif raw == "on":
                        virtual_args["checktype"] = Checktype.on
                    elif raw == "ping":
                        virtual_args["checktype"] = Checktype.ping
                    elif raw == "negotiate_connect":
                        virtual_args["checktype"] = Checktype.negotiate_connect
                    else:
                        __illegal_config_value(section, key, cur_section[key],
                                               "connect, external, negotiate, off, on, ping, negotiate_connect")
                elif key == "scheduler":
                    raw = cur_section[key]
                    if raw == "rr":
                        virtual_args["scheduler"] = Scheduler.rr
                    elif raw == "wrr":
                        virtual_args["scheduler"] = Scheduler.wrr
                    elif raw == "lc":
                        virtual_args["scheduler"] = Scheduler.lc
                    elif raw == "wlc":
                        virtual_args["scheduler"] = Scheduler.wlc
                    elif raw == "lblc":
                        virtual_args["scheduler"] = Scheduler.lblc
                    elif raw == "lblcr":
                        virtual_args["scheduler"] = Scheduler.lblcr
                    elif raw == "dh":
                        virtual_args["scheduler"] = Scheduler.dh
                    elif raw == "sh":
                        virtual_args["scheduler"] = Scheduler.sh
                    elif raw == "sed":
                        virtual_args["scheduler"] = Scheduler.sed
                    elif raw == "nq":
                        virtual_args["scheduler"] = Scheduler.nq
                    else:
                        __illegal_config_value(section, key, cur_section[key],
                                               "rr, wrr, lc, wlc, lblc, lblcr, dh, sh, sed, nq")
                elif key == "httpmethod":
                    raw = cur_section[key]
                    if raw == "get":
                        virtual_args["httpmethod"] = HTTPMethod.get
                    elif raw == "head":
                        virtual_args["httpmethod"] = HTTPMethod.head
                    else:
                        __illegal_config_value(section, key, cur_section[key], "get, head")
                elif key == "emailalert":
                    virtual_args["emailalert"] = cur_section[key]
                elif key == "emailalertfrom":
                    virtual_args["emailalertfrom"] = cur_section[key]
                elif key == "emailalertfreq":
                    try:
                        virtual_args["emailalertfreq"] = int(cur_section[key])
                        if not 0 <= virtual_args["emailalertfreq"]:
                            __illegal_config_value(section, key, cur_section[key], "0 <= emailalertfreq")
                    except ValueError:
                        __illegal_config_value(section, key, cur_section[key], "0 <= emailalertfreq")
                elif key == "service":
                    virtual_args["service"] = cur_section[key]
                elif key == "checkcommand":
                    virtual_args["checkcommand"] = cur_section[key]
                elif key == "hostname":
                    virtual_args["hostname"] = cur_section[key]
                elif key == "login":
                    virtual_args["login"] = cur_section[key]
                elif key == "passwd":
                    virtual_args["passwd"] = cur_section[key]
                elif key == "database":
                    virtual_args["database"] = cur_section[key]
                elif key == "secret":
                    virtual_args["secret"] = cur_section[key]
                elif key == "request":
                    virtual_args["request"] = cur_section[key]
                elif key == "receive":
                    virtual_args["receive"] = cur_section[key]
                else:
                    print("CUSTOM ATTRIBUTE: %s = %s" % (key, cur_section[key]))
                    virtual_args[key] = cur_section[key]

            # create virtual server and add real servers as well as the fallback server
            virtual = Virtual4(**virtual_args)
            virtual.set_fallback(fallback)
            for real in reals:
                virtual.add_real(real)
            virtuals.append(virtual)

    return global_config, virtuals
