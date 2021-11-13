'''
Load all configuration files in dir `naive_spider/config/`
'''
import yaml
import json
from ..basic import design_mode as dm
from ..basic import const


class ConfigFileLoader:
    def __init__(self, config_file):
        self.config_file = config_file

    def __call__(self, cls):
        files = self.config_file
        if isinstance(files, str):
            files = [files]
        
        d = {}
        for file in files:
            if file.endswith('yaml') or file.endswith('yml'):
                with open(file, 'r', encoding='utf-8') as f:
                    d = yaml.load(f, Loader=yaml.FullLoader)
            elif file.endswith('json'):
                with open(file, 'r', encoding='utf-8') as f:
                    d = json.load(f)
            
        cls.d = d
        return cls

class DbConn:
    def __init__(self, dt_name, d) -> None:
        '''
        dt_name: name of data table
        d: configuration dictionary
        '''
        self.table = dt_name
        self.db = d['db']
        # self.env = d['env']
        self.server = d['server']
        self.host = d['host']
        self.user = d['user']
        self.pass_ = d['pass']

@ConfigFileLoader(const.DB_CONFIG)
class DbConns(dm.Singleton):
    def __new__(cls, *args, **kwargs):
        inst = super(DbConns, cls).__new__(cls, *args, **kwargs)
        if not hasattr(inst, 'dcs'):
            inst.dcs = {k: DbConn(k, cls.d[k]) for k in cls.d}
        return inst

    def register(self, dbconn):
        if dbconn.table not in self.dcs:
            self.dcs[dbconn.table] = dbconn
    
    def get(self, dt_name):
        return self.dcs.get(dt_name)

@ConfigFileLoader(const.DS_CONFIG)
class DataSources(dm.Singleton):
    def __new__(cls, *args, **kwargs):
        inst = super(DataSources, cls).__new__(cls, *args, **kwargs)
        inst.dss = {}
        for k in inst.d:
            v = inst.d[k]
            areas = [v['province'], v.get('city')]
            area_s = const.CONNECTOR.join(a for a in areas if a)
            v['url'] = k
            del v['province']
            if 'city' in v:
                del v['city']
            inst.dss[area_s] = v
        return inst

    def get(self, area):
        if isinstance(area, str):
            return self.dss.get(area)
        elif isinstance(area, (tuple, list)):
            return self.dss.get('-'.join(area))
        raise TypeError('area must be str or tuple or list')


def DbConns_unittest():
    dbc1 = DbConns()
    dbc2 = DbConns()
    print("DbConns_unittest:", 'pass' if id(dbc1)==id(dbc2) else 'fail')

