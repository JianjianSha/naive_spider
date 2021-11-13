# io for database
# I use short connections instead of long connections to avoid the problem of thread safety.
# Of course, we can use a connection pool to strike a balance between thread safety and 
# connection efficiency. A good implementation of the connection pool is SqlAlchemy.pool.
#
# he suffix meanings are:
#   - ms: mssql/sql server
#   - my: mysql
#   - re: redis


from datetime import datetime
from pickle import NONE
from colorama.ansi import Cursor
from numpy import double
from ..basic.design_mode import Singleton
import pymssql
import redis
from functools import wraps
from ..utils import config
from ..utils.tool import *

def insert_sql(o):
    '''
    Convert a python object in database.

    ::param
        o: An object to be saved into database

    NOTICE: o must belongs to a subclass of scrapy.Item
    '''
    # s = config.Tbl_Schemas()[o.__class__.__name__]
    d = o._values
    return 'insert into {} ({}) values({})'.format(
        getattr(o, '__tablename__', o.__class__.__name__), ','.join(d.keys()), 
        ','.join(["\'%s\'" % v for v in d.values()])
    )

def value2sql(v):
    if isinstance(v, (int, float)):
        return f"{v}"
    elif isinstance(v, str):
        return f"'{v}'"


def update_sql(o):
    d = o._values
    ucs = o.unique_cols
    wheres = []
    for c in ucs:
        if c in d:
            wheres.append(f"{c}={value2sql(d[c])}")
        else:
            return False
    if not wheres:
        return False
    sets = []
    for k in d:
        if k not in ucs:
            sets.append(f"{k}={value2sql(d[k])}")
    if not sets:
        return False
    return '''update {} set {} where {}'''.format(
        getattr(o, '__tablename__', o.__class__.__name__), 
        ','.join(sets),
        ' and '.join(wheres)
    )


def insertmany_sql(os):
    '''
    Get the sql statement which represents inserting a batch of objects by pymssql.

    ::param
        os: A list of objects, whose type is a subclass of `scrapy.Item`.

    NOTICE: All objects should have the same fields that are value-assigned and the 
        same fields that are not value-assigned.
    '''
    o = os[0]
    d = o._values
    sql = "insert into {} () values ({})".format(
        getattr(o, '__tablename__', o.__class__.__name__),
        ','.join(d.keys()),
        ','.join(['%s'] * len(d))
    )
    return sql, [tuple(o_.values.values()) for o_ in os]


def selectone_sql(o):
    '''
    Convert a selection represented by python object to sql statement.
    This selection will give out one data row.

    ::param
        o: the python object which contains all infos of a database selection process.
            This object must be an instance of a subclass of `scrapy.Item`
    '''
    clauses = ["{}='{}'".format(k, v) if isinstance(v, str) else "{}={}".format(k, v) 
               for k, v in o._values.items()]

    return 'select top 1 * from {} where {}'.format(
        getattr(o, '__tablename__', o.__class__.__name__), ' and '.join(clauses)
    )




def selectmany_sql(o):
    '''
    Convert a selection represented by python object to sql statement.
    This selection will give out many data rows.

    ::param
        o: the python object which contains all infos of a database selection process.
            This object must be an instance of a subclass of `scrapy.Item`
    '''
    clauses = []
    for k, v in o._values.items():
        if isinstance(v, DbList):
            clauses.append("{} in {}".format(k, v))
        elif isinstance(v, DbRange):
            clauses.append(str(v).format(*([k]*v.c)))
        elif isinstance(v, DbFilter):
            clauses.append(str(v))
        else:
            clauses.append("{}='{}'".format(k, v) if isinstance(v, str) else "{}={}".format(k, v))
    if clauses:
        return "select * from {} where {}".format(
            getattr(o, '__tablename__', o.__class__.__name__), ' and '.join(clauses))
    return "select * from {}".format(
        getattr(o, '__tablename__', o.__class__.__name__))


def decorate_row2obj(f):
    '''
    Convert database rows to python objects.

    NOTICE: The first positional param of func `f` must be an instance
        of a subclass of `scrapy.Item`
    '''
    @wraps(f)
    def decorated(o, **kwargs):
        rows = f(o, **kwargs)
        if rows is None:
            return None
        cls = o.__class__

        if isinstance(rows, dict):
            return cls(**rows)
        return [cls(**row) for row in rows]
    return decorated



def decorate_dbconn_ms(f):
    '''
    The only positional param `o` of func `f` must has the type `scrapy.Item` or `config.Tbl_Schema`
    '''
    @wraps(f)
    def decorated(o, **kwargs):
        s = o if isinstance(o, config.DbConn) else config.DbConns().get(o.__class__.__name__)
        with pymssql.connect(server=s.host, 
                             user=s.user, 
                             password=s.pass_, 
                             database=s.db) as conn:
            with conn.cursor(as_dict=True) as cursor:
                kwargs['cursor'] = cursor
                res = f(o, **kwargs)
                fname = f.__name__
                if fname.startswith('update') or fname.startswith('insert'):
                    conn.commit()

                return res
    return decorated

@decorate_dbconn_ms
def get_columns_with_unique_index(dbconn, cursor=None):
    try:
        sql = '''
        select 
            tablename = t.name,
            indexname = ind.name,
            columnname = col.name
        from
            sys.indexes ind
        inner join
            sys.index_columns ic on ind.object_id = ic.object_id and ind.index_id = ic.index_id
        inner join
            sys.columns col on ic.object_id = col.object_id and ic.column_id = col.column_id
        inner join
            sys.tables t on ind.object_id = t.object_id
        where
            ind.is_unique = 1 and ind.is_primary_key = 0 and t.name = '%s'
        ''' % dbconn.table
        cursor.execute(sql)
        rows = cursor.fetchall()
        if rows:
            return [row['columnname'] for row in rows]
        return None
    except Exception as e:
        return None


@decorate_dbconn_ms
def update_ms(o, cursor=None):
    try:
        sql = update_sql(o)
        if not sql:
            return -1
        cursor.execute(sql)
        return 1
    except Exception as e:
        cprint('=> update error', e, color='red')
        cprint('the related sql:', sql, color='red')
        return 0

@decorate_dbconn_ms
def insert_ms(o, cursor=None):
    '''
    Insert an object into the database table
    
    ::param
        o: the object to be inserted. `o` must have the type of a subclass of `scrapy.Item`.
        cursor: please do not assign it explicitly.
    '''
    try:
        # print('=> try to insert', o.key_info())
        cursor.execute(insert_sql(o))
        return 1
    except Exception as e:
        
        if 'duplicate key' in str(e):
            return -1
        cprint('=> insert error:', e, color='red')
        return 0


@decorate_dbconn_ms
def insertmany_ms(os, cursor=None):
    '''
    Insert many python objects(a batch) into database.

    ::param
        os: A list of python objects
    '''
    assert os, "os should be a non-empty list of objects"
    try:
        cursor.executemany(*insertmany_sql(os))
        return True
    except:
        return False


@decorate_row2obj
@decorate_dbconn_ms
def selectone_ms(o, cursor=None):
    '''
    Select just one record/object from the database table. 
    `o` must have the type of a subclass of `scrapy.Item`.
    All filter conditions should be provided with the form of 
        o.xxx=yyy
        o.aaa=bbb
        ...
        i.e., by assigning values to some fields of `o`, and then
        the selection with filtering are done like:
        select top 1 * from [table_name] where xxx=yyy and aaa=bbb
    '''
    try:
        cursor.execute(selectone_sql(o))
        return cursor.fetchone()
    except Exception as e:
        tbl_name = getattr(o, '__tablename__', o.__class__.__name__)
        if f"Invalid object name '{tbl_name}'" in str(e):
            # get_logger().warning(str(e))
            return None
        else:
            raise e


@decorate_row2obj
@decorate_dbconn_ms
def selectmany_ms(o, cursor=None):
    '''
    Select many records/objects from the database table.
    `o` is used to provide table schema and filter conditions etc.
    For range filtering, there are three kinds of type as following:
    1. o.xxx=yyy
    2. o.aaa=DbList([1,2,3])
    3. o.ddd=DbRange(10, 100)
    Then the translated sql statement is like:
    select * from [table_name] where xxx=yyy and aaa in [1,2,3] and ddd >= 10 and ddd < 1000
    '''
    try:
        cursor.execute(selectmany_sql(o))
        return cursor.fetchall()
    except Exception as e:
        tbl_name = getattr(o, '__tablename__', o.__class__.__name__),
        if f"Invalid object name '{tbl_name}'" in str(e):
            # get_logger().warning(str(e))
            return []
        else:
            raise e


@decorate_dbconn_ms
def get_columns(o, cursor=None):
    assert isinstance(o, config.DbConn), \
        "param `o` must has the type `config.DbConn` currently."
    sql = "SELECT [name] FROM sys.columns where [object_id] = " + \
            "(SELECT [object_id] FROM sys.tables WHERE [name] = '{}')".format(o.table)
    cursor.execute(sql)
    return cursor.fetchall()


class DbRange:
    def __init__(self, _min, _max):
        if _min is None and _max is None:
            raise "Parameters min_ and _max cannot be None at the same time."
        
        if _min is not None and _max is not None:
            self.c = 2
            assert type(_min) is type(_max), "Type of _min and _max must be the same."
        else:
            self.c = 1

        if _min is not None:
            t1 = type(_min)
            assert getattr(t1, '__eq__') and getattr(t1, '__lt__'), \
                "Type of _min doesn't support full comparion operations"
        if _max is not None:
            t2 = type(_max)
            assert getattr(t2, '__eq__') and getattr(t2, '__lt__'), \
                "Type of _max doesn't support full comparion operations"
        self._min=_min
        self._max=_max

    def __str__(self):
        if self._min is not None and self._max is not None:
            return f"{{}} >= '{self._min}' and {{}} < '{self._max}'" if isinstance(self._min, str) \
                else f"{{}} >= {self._min} and {{}} < {self._max}"
        elif self._min is not None:
            return f"{{}} >= '{self._min}'" if isinstance(self._min, str) else f"{{}} >= {self._min}"
        else:
            return f"{{}} < '{self._max}'" if isinstance(self._max, str) else f"{{}} < {self._max}"


class DbList:
    def __init__(self, _list):
        assert _list and isinstance(_list, list), "_list must not be None and not be empty."
        t = type(_list[0])
        for e in _list:
            if not isinstance(e, t):
                raise "Type of all elements in _list must be the same."
        self._list = _list

    def __str__(self):
        if isinstance(self._list[0], str):
            return '[{}]'.format(','.join(["'%s'" % e for e in self._list]))
        else:
            return '[{}]'.format(','.join([str(e) for e in self._list]))


class DbFilter:
    def __init__(self, filter):
        self.filter = filter
    
    def __str__(self):
        return self.filter


class RedisClients(Singleton):
    def get_client(self, ts):
        if not hasattr(self, 'd'):
            self.clients = {}
        client = self.clients.get(ts.table)
        if client is None:
            # cc = config.DbConnDict().get_dbconn(ts.server, ts.host)
            # dbconn = redis.ConnectionPool(host=ts.host, 
            #                               port=cc.port, db=cc.db, password=cc.pass_)
            # self.d[ts.host] = dbconn
            # use long connection, so it does not need to maintain a ConnectionPool since
            # each redis client will keep a connection pool itself.
            client = redis.Redis(host=ts.host, port=ts.port, password=ts.pass_, db=ts.db, decode_responses=True)
            self.clients[ts.table] = client
        return client
            
def get_redis(name):
    '''name: name of Table, or whatever you want, such as "ProxyIp", see config/tbl_schemas.yaml'''
    return RedisClients().get_client(config.Tbl_Schemas()[name])
     
# Because there are a large amount of usage cases which are too trivial to elegantly 
# implement them, I will supply the corresponding methods later, according to needs 
# on the occasion.

# In the following part, I will turn to sqlalchemy for a flexible and strong
# databas IO. (This function development is delayed, even canceled in future.)



def test():
    a = 'str'
    b = 'rts'
    c = DbRange(a, b)
    d = DbRange(12, 2)
    try:
        e = DbRange(c, d)       # Failed
    except Exception as ex:
        print(ex)
    
    try:
        f = DbList([1])
    except Exception as ex:
        print(ex)