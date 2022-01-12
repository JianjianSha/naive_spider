from scrapy import Item, Field
from scrapy.item import ItemMeta, DictItem
from ..utils.config import DbConn, DbConns
from ..pipelines import dba


def key_info(self):
    es = []
    if self.unique_cols is not None:
        for c in self.unique_cols:
            v = self[c] if c in self._values else '<None>'
            es.append(f"{c}={v}")
    for c in self._values:
        if 'name' in c.lower() or 'province' in c.lower():
            es.append(f"{c}={self[c]}")
            break

    es.append('...')
    return "[%s]" % (', '.join(es))

class ConfigDbConn:
    def __init__(self, **kwargs):
        '''
        kwargs: must contain keys: server, db, env, host. Keys' order is free.
        '''
        self.kwargs = kwargs

    def __call__(self, cls):
        dbconn = DbConns().get(cls.__name__)
        if dbconn is None:
            assert self.kwargs, f"no db connections found for '{cls.__name__}'"\
                " in db.yml or ConfigDbConn construction parameters"

            dbconn = dbconn(cls.__name__, self.kwargs)
            DbConns().register()
        
        if not hasattr(dbconn, 'fields'):
            dbconn.fields = [row['name'] for row in dba.get_columns(dbconn)]
        # cls.fields = {field: Field() for field in dbconn.fields}
        return cls


class ModelMeta(ItemMeta):
    def __new__(cls, name, bases, kwargs):
        fields = {}
        new_attrs = {}
        dt_name = name[:-4] if name.endswith('Item') else name
        dbconn = DbConns().get(dt_name)
        
        for field in [row['name'] for row in dba.get_columns(dbconn)]:
            fields[field] = Field()

        new_attrs['fields'] = fields
        for k in kwargs:
            new_attrs[k] = kwargs[k]
        if '__tablename__' not in new_attrs:
            new_attrs['__tablename__'] = name

        new_attrs['unique_cols'] = dba.get_columns_with_unique_index(dbconn)
        new_attrs['key_info'] = key_info
        
        return super().__new__(cls, name, (Item,), new_attrs)

    
        
                


class InvestProject(metaclass=ModelMeta):
    pass


class InvestApprove(metaclass=ModelMeta):
    pass


