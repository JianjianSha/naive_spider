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
        if self.province_zh[-1] != '省' and self.province_zh not in MUNICIPALITIES:
            return self.province_zh + '省'
        return self.province_zh
    
    @property
    def city(self):
        if self.province_zh in MUNICIPALITIES:
            city = self.province_zh
            if city[-1] != '市':
                city += '市'
        return self.city_zh
         
    def start_requests(self):
        yield self.request.request()

    def parse(self, response):
        req = response.meta['r']
        try:
            text = response.body.decode(chardet.detect(response.body)['encoding'])
        except:
            text = response.text

        soup = BeautifulSoup(text, 'lxml')

        if isinstance(req, PageDetailRequest):
            data = self.isomorphic_extract_data(soup, req.config)
            for item in self.package(req.data, data):
                yield item
        else:
            
            if req.counter == 0:
                r = request.Request(req.config['yzm_url'], headers=req.headers)
                resp = request.urlopen(r, timeout=30)
                img = resp.read()
                img = base64.b64encode(img)
                d = urlparse.urlencode({'img': img}).encode('utf-8')
                r = request.Request("http://0.0.0.0:1234/sh", data=d)
                resp = request.urlopen(r, timeout=30)
                img_code = resp.read().decode('utf-8', errors='ignore')
                print("captcha:", img_code)
                req.set_captcha(img_code)
            else:
                if req.config.get('yzm_url'):
                    req.reset_captcha()
                green_print('=> get response from url:', response.url)
                # self.dump_page(text)
                datas = self.isomorphic_extract_data(soup, req.config['list'], req.config['params'])
                for data in datas:
                    # print(data)
                    dr = PageDetailRequest(data, req.config['detail'])
                    time.sleep(REQUEST_SPAN)
                    yield dr.request()

                self.logger.warning('url: ' + response.url)
                if DEBUG: return        # do not go on next page crawling

            time.sleep(REQUEST_SPAN)
            req.page_next()
            yield req.request()
    
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
                if not v:
                    data[k] = ''
                    continue
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

    def package(self, ld, dd):
        ip = InvestProject()
        ip['ip_code'] = dd.get('code', ld.get('code'))
        ip['ip_name'] = dd.get('name', ld.get('name'))
        ip['ip_construction'] = dd.get('frdw', '')
        ip['ip_projtype'] = dd.get('xmlb', '')
        ip['ip_province'] = self.province
        ip['ip_city'] = self.city
        ip['ip_status'] = ld.get('spjg', '')
        ip['ip_date'] = ld.get('sprq')
        ip['ip_createuser'] = 'sjj'
        ip['ip_createtime'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        ip['ip_url'] = ld.get('url_', '')
        ip['ip_updatetime'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        ip['ip_oragan'] = ld.get('spbm', '')

        ias = []
        for xx in dd.get('gsxx', [])+dd.get('bljg', []):
            ia = InvestApprove()
            ia['ip_code'] = ip['ip_code']
            ia['ia_dept'] = xx.get('spbm', ip['ip_oragan'])
            ia['ia_item'] = xx.get('spsx')
            ia['ia_status'] = xx.get('spjg', ip['ip_status'])
            ia['ia_date'] = xx.get('sprq', ip['ip_date'])
            ia['ia_permissionnum'] = xx.get('spwh', '')
            ia['ia_code'] = md5_16(ia['ip_code']+(ia['ia_dept'] or '') + \
                (ia['ia_item'] or '') + (ia['ia_status'] or '') + (ia['ia_date'] or '')\
                    + (ia['ia_permissionnum'] or '') + '')
            ias.append(ia)
        
        if not self.city:
            depart = ip['ip_oragan']
            if not depart and ias:
                depart = ias[0]['ia_dept']
            ip['ip_city'] = area.guess_city(depart, self.province_zh)
            if not ip['ip_city']:
                ip['ip_city'] = area.guess_city(ip['ip_construction'], self.province_zh)
            if not ip['ip_city']:
                ip['ip_city'] = area.guess_city(ip['ip_name'], self.province_zh) or ''

        return ip, *ias

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
        if k == 'url_' and v:
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

        self.headers = self.config.get('headers', {})
        if self.config.get('yzm_enabled', 0) == 0:
            self.config['yzm_url'] = ''
        self.counter = 0 if self.config.get('yzm_url') else 1

    @property
    def url(self):
        return self.config['url']

    @property
    def page(self):
        return self.page_

    def page_next(self):
        self.counter += 1
        if self.counter != 1:
            self.page_ += 1
        
    def set_captcha(self, captcha):
        self.config['params']['qryYZM'] = captcha

    def reset_captcha(self):
        self.config['params']['qryYZM'] = ''

    def request(self, **kwargs):
        args = {'wait': 5, 'timeout': 60, 'images': 0, 'resource_timeout': 20}
        url = self.url
        if 'params' in self.config and self.counter > 0:
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