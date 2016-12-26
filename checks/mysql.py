from twisted.enterprise import adbapi
from twisted.python.failure import Failure

from UnexpectedResult import UnexpectedResult


def __cb_close_pool(ret, pool, global_config):
    try:
        pool.close()
    except Exception as e:
        global_config.log.error("Closing the MySQL connection pool failed: %s" % str(e))

    if isinstance(ret, Failure):
        ret.raiseException()
    else:
        return ret


def __cb_check_value(value):
    if value is None or len(value) == 0:
        raise UnexpectedResult("got nothing, expected something")


def __cb_error(reason):
    reason.raiseException()


def check(virtual, real, global_config):
    pool = adbapi.ConnectionPool("MySQLdb", host=real.ip.exploded, port=real.port, user=virtual.login,
                                 passwd=virtual.passwd, db=virtual.database)
    d = pool.runQuery(virtual.request, ())
    d.addBoth(__cb_close_pool, pool, global_config)
    d.addErrback(__cb_error)
    d.addCallback(__cb_check_value)
    return d
