'''
DO WHAT THE FUCK YOU WANT TO PUBLIC LICENSE

Copyright (c) 2021 Jianjian Sha <501834524@qq.com>
'''
from scrapy.http import headers
from scrapy_splash.request import SplashFormRequest
from .imports import *

class BaseSpider(scrapy.Spider):
    def __init__(self, city=None):
        '''
        city: city name or pinyin.
            If is pinyin, it must be roma pinyin
        '''
        self.province_py = self.name
        self.province_zh = area.py2name(self.province_py)
        self.city_zh = city
        if city:
            if all(ord(c) < 128 for c in city):
                self.city_zh = area.py2name(city)
                city_py = city
            else:
                city_py = roma_py(city)
            area_s = self.province_py + CONNECTOR + city_py
        else:
            area_s = self.province_py

        ds_config = DataSources().get(area_s)
        self.request = PageListRequest(config=ds_config)

    @property
    def province(self):
        if self.province_zh[-1] != '省':
            return self.province_zh + '省'
        return self.province_zh
    
    @property
    def city(self):
        return self.city_zh
         
    def start_requests(self):
        yield self.request.request()

    def parse(self, response):
        request = response.meta['r']
        try:
            text = response.body.decode(chardet.detect(response.body)['encoding'])
        except:
            text = response.text

        soup = BeautifulSoup(text, 'lxml')

        if isinstance(request, PageDetailRequest):
            data = self.isomorphic_extract_data(soup, request.config)
            for item in self.package(request.data, data):
                yield item
        else:
            green_print('=> get response from url:', response.url)
            datas = self.isomorphic_extract_data(soup, request.config['list'], request.config['params'])
            for data in datas:
                dr = PageDetailRequest(data, request.config['detail'])
                time.sleep(REQUEST_SPAN)
                yield dr.request()

            self.logger.warning('url:', response.url)
            if DEBUG: return        # do not go on next page crawling

            time.sleep(REQUEST_SPAN)
            request.page_next()
            yield request.request()
    
    def isomorphic_extract_data(self, soup, config, params=None):
        '''
        Extract data from webpage and keep the extracted data struct isomorphic with the field
        struct in configuration file. To be more basically,  the basespider should not do any
        work out of range of extracting data from webpage, i.e. basespider just extracts data
        according to the configuration and the subsequent work of packaging data into one model 
        entity(or more) should be implemented by concrete task spider (a child class of base
        -spider), since different tasks usually use different model entities (such as model
        class name, field name, etc.).

        @parameters:
        config: field configuration. It commonly has a form of dictionary.
        soup: a BeautifulSoup object, which built on the whole page html.
        '''
        def _extract_one(t, c):
            nonlocal params
            data = {}
            for k, v in c.items():
                if k[0] == '_': continue
                if isinstance(v, str):
                    value = get_tag(t, v)
                    data[k] = self.post_process(k, value, params)
                elif isinstance(v, dict):
                    data[k] = _extract_recur(t, v)
            return data
        
        def _extract_recur(t, c):
            if '_items' in c:
                datas = []
                tags = get_tag(t, c['_items'])
                if tags is None:
                    return datas
                for tag in tags:
                    datas.append(_extract_one(tag, c))
                return datas
            return _extract_one(t, c)
        return _extract_recur(soup, config)

    def package(self, list_data, dtl_data):
        pass

    def dump_page(self, text):
        '''
        Dump the html content of a page. This function is just for debug.
        '''
        with open('logs/%s.html' % self.name, 'w') as f:
            f.write(text)
    
    def build_detail_url(self, fake_url, config):
        '''
        rebuild the detail url
        '''
        pass

    def post_process(self, k, v, config):
        if k == 'url_':
            if v[:4] != 'http':
                v = self.build_detail_url(v, config)
        # if k.endswith('rq'):
        #     parse_time_from_text(v)
        return v



class BaseSpiderMeta(type):
    def __new__(cls, name, bases, kwargs):
        return super().__new__(cls, name, (BaseSpider,), kwargs)

    def __init__(cls, name, bases, namespace, **kwargs):
        cls.name = cls.__name__.lower()
        return super().__init__(name, bases, kwargs)


class PageListRequest:
    def __init__(self, **kwargs):
        self.config = kwargs['config']
        # self.data = kwargs['data']
        if self.config['method'] == 'post':
            self.page_key = self.config['page_key'] \
                if 'page_key' in self.config else 'page'
            self.page_ = self.config['params'][self.page_key]

        self.headers = {}

    @property
    def url(self):
        return self.config['url']

    @property
    def page(self):
        return self.page_

    def page_next(self):
        self.page_ += 1

    def request(self, **kwargs):
        args = {'wait': 5, 'timeout': 60, 'images': 0, 'resource_timeout': 20}
        url = self.url
        if 'params' in self.config:
            self.config['params'][self.page_key] = self.page
            params = []
            for k, v in self.config['params'].items():
                params.append('%s=%s' % (k, str(v)))
            url = self.url + '?' + '&'.join(params)
        return SplashRequest(url, meta={'r': self}, args=args, headers=self.headers) if SPLASH \
                else scrapy.Request(url, meta={'r': self}, headers=self.headers)
        

class PageDetailRequest:
    def __init__(self, data, config) -> None:
        self.data = data
        self.config = config
    
    def request(self):
        args = {'wait': 5, 'timeout': 60, 'images': 0, 'resource_timeout': 20}
        return SplashRequest(self.data['url_'], meta={'r': self}, args=args, headers={}) if SPLASH else \
            scrapy.Request(self.data['url_'], meta={'r':self}, headers={})