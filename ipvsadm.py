import subprocess

from twisted.internet import reactor
from twisted.internet.protocol import ProcessProtocol

import external
from enums import *


def initial_ipvs_setup(virtuals, global_config):
    for virtual in virtuals:
        quiescent = virtual.quiescent if virtual.quiescent is not None else global_config.quiescent

        # delete the virtual service in case it might be present
        try:
            delete_virtual_service(virtual, global_config, True)
        except subprocess.CalledProcessError:
            # TODO: sensible logging
            pass  # this will happen quite often

        # add the virtual service
        add_virtual_service(virtual, global_config, True)

        # loop all real servers and set them up if we quiescent
        if quiescent:
            for real in virtual.real:
                add_real_server(virtual, real, global_config, True)

        # add the fallback if it exists
        if virtual.fallback is not None:
            add_real_server(virtual, virtual.fallback, global_config, True)


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

    print(args)

    # execute the prepared command
    if sync:
        args[0] = external.ipvsadm_path
        subprocess.check_call(args)
    else:
        reactor.spawnProcess(__IPVSProcessProtocol(), external.ipvsadm_path, args, {})

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

    print(args)

    # execute the prepared command
    if sync:
        args[0] = external.ipvsadm_path
        subprocess.check_call(args)
    else:
        reactor.spawnProcess(__IPVSProcessProtocol(), external.ipvsadm_path, args, {})

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

    print(args)

    # execute the prepared command
    if sync:
        args[0] = external.ipvsadm_path
        subprocess.check_call(args)
    else:
        reactor.spawnProcess(__IPVSProcessProtocol(), external.ipvsadm_path, args, {})

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

    print(args)

    # execute the prepared command
    if sync:
        args[0] = external.ipvsadm_path
        subprocess.check_call(args)
    else:
        reactor.spawnProcess(__IPVSProcessProtocol(), external.ipvsadm_path, args, {})

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

    print(args)

    # execute the prepared command
    if sync:
        args[0] = external.ipvsadm_path
        subprocess.check_call(args)
    else:
        reactor.spawnProcess(__IPVSProcessProtocol(), external.ipvsadm_path, args, {})

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

    print(args)

    # execute the prepared command
    if sync:
        args[0] = external.ipvsadm_path
        subprocess.check_call(args)
    else:
        reactor.spawnProcess(__IPVSProcessProtocol(), external.ipvsadm_path, args, {})

    # set is_present
    real.is_present = True


class __IPVSProcessProtocol(ProcessProtocol):
    def connectionMade(self):
        self.transport.closeStdin()

    def errReceived(self, data):
        print("stderr: " + data)

    def outReceived(self, data):
        print("stdout: " + data)
