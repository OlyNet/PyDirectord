import subprocess
import sys

from twisted.internet import reactor
from twisted.internet.protocol import ProcessProtocol

import external
from enums import *


def initial_ipvs_setup(virtuals, global_config):
    global_config.log.debug("Beginning initial ipvs table setup")
    for virtual in virtuals:
        virtual_hostname = virtual.ip.exploded + ":" + str(virtual.port)

        # delete the virtual service in case it might be present
        try:
            delete_virtual_service(virtual, global_config, True)
        except subprocess.CalledProcessError:
            global_config.log.debug(
                "Deleting the virtual service for " + virtual_hostname + " failed during initialization (probably ok)")

        # add the virtual service
        global_config.log.info("Adding virtual service for " + virtual_hostname)
        try:
            add_virtual_service(virtual, global_config, True)
        except subprocess.CalledProcessError:
            global_config.log.critical(
                "Adding the virtual service for " + virtual_hostname + " failed during initialization")
            sys.exit(1)

        # loop all real servers and set them up if we quiescent
        if virtual.quiescent:
            for real in virtual.real:
                real_hostname = real.ip.exploded + ":" + str(real.port)
                global_config.log.info("Adding real server " + real_hostname)
                try:
                    add_real_server(virtual, real, global_config, True)
                except subprocess.CalledProcessError:
                    global_config.log.critical(
                        "Adding the real server " + real_hostname + " failed during initialization")
                    sys.exit(1)

        # add the fallback if it exists
        if virtual.fallback is not None:
            global_config.log.info("Adding fallback server for " + virtual_hostname)
            try:
                add_real_server(virtual, virtual.fallback, global_config, True)
            except:
                global_config.log.critical(
                    "Adding the fallback server for " + virtual_hostname + " failed during initialization")
                sys.exit(1)
    global_config.log.debug("Initial ipvs table setup done")


def add_virtual_service(virtual, global_config, sync=False):
    args = [external.ipvsadm_name, "-A"]

    # use correct protocol
    if virtual.protocol == Protocol.tcp:
        args.append("-t")
    elif virtual.protocol == Protocol.udp:
        args.append("-u")
    elif virtual.protocol == Protocol.fwm:
        raise NotImplementedError("firewall-marks are not implemented yet")
    else:
        raise ValueError

    # set virtual hostname
    virtual_hostname = virtual.ip.exploded + ":" + str(virtual.port)
    args.append(virtual_hostname)

    # set scheduler
    args.append("-s")
    args.append(virtual.scheduler.name)

    global_config.log.debug(args)

    # execute the prepared command
    if sync:
        args[0] = external.ipvsadm_path
        subprocess.run(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).check_returncode()
    else:
        reactor.spawnProcess(__IPVSProcessProtocol(global_config), external.ipvsadm_path, args, {})

    # set is_present
    virtual.is_present = True


def delete_virtual_service(virtual, global_config, sync=False):
    args = [external.ipvsadm_name, "-D"]

    # use correct protocol
    if virtual.protocol == Protocol.tcp:
        args.append("-t")
    elif virtual.protocol == Protocol.udp:
        args.append("-u")
    elif virtual.protocol == Protocol.fwm:
        raise NotImplementedError("firewall-marks are not implemented yet")
    else:
        raise ValueError

    # set virtual hostname
    virtual_hostname = virtual.ip.exploded + ":" + str(virtual.port)
    args.append(virtual_hostname)

    global_config.log.debug(args)

    # execute the prepared command
    if sync:
        args[0] = external.ipvsadm_path
        subprocess.run(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).check_returncode()
    else:
        reactor.spawnProcess(__IPVSProcessProtocol(global_config), external.ipvsadm_path, args, {})

    # set is_present
    virtual.is_present = False


def edit_virtual_service(virtual, global_config, sync=False):
    args = [external.ipvsadm_name, "-E"]

    # use correct protocol
    if virtual.protocol == Protocol.tcp:
        args.append("-t")
    elif virtual.protocol == Protocol.udp:
        args.append("-u")
    elif virtual.protocol == Protocol.fwm:
        raise NotImplementedError("firewall-marks are not implemented yet")
    else:
        raise ValueError

    # set virtual hostname
    virtual_hostname = virtual.ip.exploded + ":" + str(virtual.port)
    args.append(virtual_hostname)

    # set scheduler
    args.append("-s")
    args.append(virtual.scheduler.name)

    global_config.log.debug(args)

    # execute the prepared command
    if sync:
        args[0] = external.ipvsadm_path
        subprocess.run(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).check_returncode()
    else:
        reactor.spawnProcess(__IPVSProcessProtocol(global_config), external.ipvsadm_path, args, {})

    # set is_present
    virtual.is_present = True


def add_real_server(virtual, real, global_config, sync=False):
    args = [external.ipvsadm_name, "-a"]

    # use correct protocol
    if virtual.protocol == Protocol.tcp:
        args.append("-t")
    elif virtual.protocol == Protocol.udp:
        args.append("-u")
    elif virtual.protocol == Protocol.fwm:
        raise NotImplementedError("firewall-marks are not implemented yet")
    else:
        raise ValueError

    # set virtual hostname
    virtual_hostname = virtual.ip.exploded + ":" + str(virtual.port)
    args.append(virtual_hostname)

    # set real hostname
    args.append("-r")
    real_hostname = real.ip.exploded + ":" + str(real.port)
    args.append(real_hostname)

    # set forwarding method
    if real.method == ForwardingMethod.gate:
        args.append("-g")
    elif real.method == ForwardingMethod.masq:
        args.append("-m")
    elif real.method == ForwardingMethod.ipip:
        args.append("-i")
    else:
        raise ValueError

    # set weight
    args.append("-w")
    args.append(str(real.current_weight))

    global_config.log.debug(args)

    # execute the prepared command
    if sync:
        args[0] = external.ipvsadm_path
        subprocess.run(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).check_returncode()
    else:
        reactor.spawnProcess(__IPVSProcessProtocol(global_config), external.ipvsadm_path, args, {})

    # set is_present
    real.is_present = True


def delete_real_server(virtual, real, global_config, sync=False):
    args = [external.ipvsadm_name, "-d"]

    # use correct protocol
    if virtual.protocol == Protocol.tcp:
        args.append("-t")
    elif virtual.protocol == Protocol.udp:
        args.append("-u")
    elif virtual.protocol == Protocol.fwm:
        raise NotImplementedError("firewall-marks are not implemented yet")
    else:
        raise ValueError

    # set virtual hostname
    virtual_hostname = virtual.ip.exploded + ":" + str(virtual.port)
    args.append(virtual_hostname)

    # set real hostname
    args.append("-r")
    real_hostname = real.ip.exploded + ":" + str(real.port)
    args.append(real_hostname)

    global_config.log.debug(args)

    # execute the prepared command
    if sync:
        args[0] = external.ipvsadm_path
        subprocess.run(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).check_returncode()
    else:
        reactor.spawnProcess(__IPVSProcessProtocol(global_config), external.ipvsadm_path, args, {})

    # set is_present
    real.is_present = False


def edit_real_server(virtual, real, global_config, sync=False):
    args = [external.ipvsadm_name, "-e"]

    # use correct protocol
    if virtual.protocol == Protocol.tcp:
        args.append("-t")
    elif virtual.protocol == Protocol.udp:
        args.append("-u")
    elif virtual.protocol == Protocol.fwm:
        raise NotImplementedError("firewall-marks are not implemented yet")
    else:
        raise ValueError

    # set virtual hostname
    virtual_hostname = virtual.ip.exploded + ":" + str(virtual.port)
    args.append(virtual_hostname)

    # set real hostname
    args.append("-r")
    real_hostname = real.ip.exploded + ":" + str(real.port)
    args.append(real_hostname)

    # set forwarding method
    if real.method == ForwardingMethod.gate:
        args.append("-g")
    elif real.method == ForwardingMethod.masq:
        args.append("-m")
    elif real.method == ForwardingMethod.ipip:
        args.append("-i")
    else:
        raise ValueError

    # set weight
    args.append("-w")
    args.append(str(real.current_weight))

    global_config.log.debug(args)

    # execute the prepared command
    if sync:
        args[0] = external.ipvsadm_path
        subprocess.run(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).check_returncode()
    else:
        reactor.spawnProcess(__IPVSProcessProtocol(global_config), external.ipvsadm_path, args, {})

    # set is_present
    real.is_present = True


class __IPVSProcessProtocol(ProcessProtocol):
    def __init__(self, global_config):
        self.global_config = global_config

    def connectionMade(self):
        self.transport.closeStdin()

    def errReceived(self, data):
        self.global_config.log.error("Error from 'ipvsadm': " + str(data))

    def outReceived(self, data):
        if data is not None:
            self.global_config.log.warning("From 'ipvsadm': " + str(data))
