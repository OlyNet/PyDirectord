from ldaptor.protocols.ldap import ldapclient
from ldaptor.protocols.ldap.ldapconnector import LDAPClientCreator
from twisted.internet import reactor


def check(virtual, real, global_config):
    basedn = virtual.request
    overrides = {basedn: (real.ip.exploded, real.port)}
    client = LDAPClientCreator(reactor, ldapclient.LDAPClient)
    client = client.connect(basedn, overrides=overrides)
    d = client.bind(virtual.login, virtual.passwd)

    return d
