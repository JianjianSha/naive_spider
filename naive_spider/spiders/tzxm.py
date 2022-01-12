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

    


class Shahnghaai(metaclass=BaseSpiderMeta):
    search_worlds_used = [
        '新能源',
        '半导体',
        '人工智能',
        '智能汽车',
        '光伏项目',
        '房项目',
        '有限公司',
        '发项目',       # yanfa, kaifa
        '改造项目',
    ]

    search_words = [
        '机械制造',
        '高科技',
        '交通设施',
        '大数据',
        
        '改造项目',
        '扩建项目',
        
        '建设项目'
    ]
    def build_detail_url(self, fake_url, config):
        pattern = r"'([^']+)'"
        id_ = re.findall(pattern, fake_url)[0]
        return "http://222.66.64.156:8082/xxgs/proInfoDetail.jsp?SHID=%s" % id_

class XProvince(metaclass=BaseSpiderMeta):
    pass



