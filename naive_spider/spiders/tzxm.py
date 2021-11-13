'''
DO WHAT THE FUCK YOU WANT TO PUBLIC LICENSE

Copyright (c) 2021 Jianjian Sha <501834524@qq.com>


Do not limit any department:
$ scrapy crawl henan

Specify some departments:
$ scrapy crawl henan -a departs=gxt,fgw

Specify a concrete city, note that the suffix '市' is needed.
We keep this kind of suffix for the sake of the diversification of cities and counties,
while for provinces, we hardcode all their suffices.
$ scrapy crawl henan -a city=zhengzhoushi

or use first letter of full pinyin
$ scrapy crawl henan -a city=zzs

To specify a county, we must specify its belonging-to city at the same time, e.g.,
$ scrapy crawl henan -a city=zhengzhoushi -a county=zhongyuanqu


1. In a word, for provinces, we use their pinyin (without suffix), while for cities and
counties, we use their full pinyin (with suffix) or first-letter abbreviation of full
pinyin. We use full hanzi (with suffix) for all level areas.

2. Please refer to items.item_gen.AreaList for more details about the full name of cities
and counties. 
'''

from scrapy.spiders import Spider
from .basespider import *


class Hebei(metaclass=BaseSpiderMeta):
    def build_detail_url(self, fake_url, config):
        url_template = 'http://tzxm.hbzwfw.gov.cn/sbglweb/xminfo?xmdm=%s&sxid=%s&xzqh=%s'
        pattern = r"'([^']+)'"
        a, b = re.findall(pattern, fake_url)
        return url_template % (a, b, config['xzqh'])

    def package(self, ld, dd):
        ip = InvestProject()
        ip['ip_code'] = dd.get('code', ld.get('code'))
        ip['ip_name'] = dd.get('name', ld.get('name'))
        ip['ip_construction'] = dd.get('frdw')
        ip['ip_projtype'] = dd.get('xmlb')
        ip['ip_province'] = self.province
        ip['ip_city'] = self.city
        ip['ip_status'] = ld.get('spjg')
        ip['ip_date'] = ld.get('sprq')
        ip['ip_createuser'] = 'sjj'
        ip['ip_createtime'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        ip['ip_url'] = ld.get('url_')
        ip['ip_updatetime'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        ip['ip_oragan'] = ld.get('spbm')

        ias = []
        for xx in dd['gsxx']+dd['bljg']:
            ia = InvestApprove()
            ia['ip_code'] = ip['ip_code']
            ia['ia_dept'] = xx.get('spbm', ip['ip_oragan'])
            ia['ia_item'] = xx.get('spsx')
            ia['ia_status'] = xx.get('spjg', ip['ip_status'])
            ia['ia_date'] = xx.get('sprq', ip['ip_date'])
            ia['ia_permissionnum'] = xx.get('spwh')
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


class XProvince(metaclass=BaseSpiderMeta):
    pass



