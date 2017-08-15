from twisted.enterprise import adbapi
from twisted.python.failure import Failure

from pydexceptions import *


def __cb_close_pool(ret, pool, global_config):
    try:
        pool.close()
    except Exception as e:
        global_config.log.error("Closing the PostgreSQL connection pool failed: %s" % str(e))

    if isinstance(ret, Failure):
        ret.raiseException()
    else:
        return ret


def __cb_check_value(value):
    if value is None or len(value) == 0:
        raise UnexpectedResultException("got nothing, expected something")


def __cb_error(reason):
    reason.raiseException()


def check(virtual, real, global_config):
    # prepare the parameters for the connection pool and perform some sanity checks
    db_args = dict()
    db_args['connect_timeout'] = virtual.negotiatetimeout
    db_args['host'] = real.ip.exploded
    db_args['port'] = virtual.checkport if virtual.checkport else real.port
    db_args['password'] = virtual.passwd if virtual.passwd else ""
    if virtual.login is None:
        raise IllegalConfigurationException("no username ('login') specified for PostgreSQL check")
    else:
        db_args['user'] = virtual.login
    if virtual.database is None:
        raise IllegalConfigurationException("no database specified for PostgreSQL check")
    else:
        db_args['database'] = virtual.database
    if virtual.request is None:
        raise IllegalConfigurationException("no query ('request') specified for PostgreSQL check")

    # initiate the connection pool and query the database
    pool = adbapi.ConnectionPool("pgdb", cp_min=1, cp_max=1, **db_args)
    d = pool.runQuery(virtual.request, ())

    # add internal checks to deferred
    d.addBoth(__cb_close_pool, pool, global_config)
    d.addErrback(__cb_error)
    d.addCallback(__cb_check_value)

    return d
