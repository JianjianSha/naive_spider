from naive_spider.items.fenshaolu import FenShaoLuItem
from .imports import *
import json
import time

class ShanghaiCaptcha(scrapy.Spider):
    name = 'shanghaicaptcha'
    # scrapy crawl shanghaicaptcha
    custom_settings = {
        'ITEM_PIPELINES': {}
    }
    def __init__(self, **kwargs):
        self.count = 0
        # self.url = 'http://222.66.64.156:8082/xxgs/CheckCodeImg2.jsp?d=%d'  # shanghai

        # fujian
        # self.url = 'http://61.154.11.191/creditpub/captcha?preset=&ra=0.07100937359923254'
        # self.task = 'fujian'
        self.url = 'https://credit.ningbo.gov.cn/nbggxy/resources/jsp/image.jsp?tm=0.014761931814312623'
        self.task = 'nbxy'
    

    def _request(self):
        url = self.url
        if '%d' in self.url:
            milisecond = int(round(time.time()*1000))
            url = self.url % milisecond
        return scrapy.Request(url, dont_filter=True)

    def start_requests(self):
        yield self._request()

    def parse(self, response):
        img = response.body
        self.count += 1
        if '%d' in self.url:
            filename = response.url.split('=')[1]
        else:
            filename = str(self.count)
        with open('naive_spider/images/%s/%s.jpg' % (self.task, filename), 'wb') as f:
            f.write(img)
            
            print('=> %d, filename: %s' % (self.count, filename))
        if self.count < 512:
            time.sleep(0.2)
            yield self._request()


class Chengyu(scrapy.Spider):
    name = 'chengyu'
    custom_settings = {
        'ITEM_PIPELINES': {
        }
    }


    def __init__(self):
        self.letter = 1
        self.page = 1
        self.url = 'https://www.chengyucidian.net/letter/%d/p/%d'

    def start_requests(self):
        yield scrapy.Request(self.url % (self.letter, self.page))

    def parse(self, response):
        print('get response from', response.url)
        try:
            text = response.body.decode(chardet.detect(response.body)['encoding'])
        except:
            text = response.text
        # print('text', text)

        soup = BeautifulSoup(text, 'lxml')
        div = soup.find('div', class_='cate')
        if div is None:
            self.letter += 1
            self.page = 1
            if self.letter <= 26:
                return self.start_requests()

        lis = div.find_all('li')
        print('len:', len(lis))
        cys = []
        for li in lis:
            a = li.find('a')
            # print('a', a)
            # print('fuck', a.get_text())
            cy = a.get_text().strip()
            # print('cy', cy, len(cy))
            if len(cy) == 4:
                cys.append(cy+'\n')
        # save to file
        if not cys:
            self.letter += 1
            self.page = 1
            if self.letter <= 26:
                return self.start_requests()
        else:
            # print(cys)
            try:
                with open('naive_spider/data/chengyu.txt', 'a') as f:
                    f.writelines(cys)
                self.page += 1
                time.sleep(0.5)
            except Exception as e:
                print(e)
            return self.start_requests()


class FenShaoLu(scrapy.Spider):
    name = 'fenshaolu'
    custom_settings = {
        'ITEM_PIPELINES': {
            'naive_spider.pipelines.file_pl.ExcelPipeline': 300,
        }
    }

    def __init__(self):
        print('initialize...')
        self.url = 'https://ljgk.envsc.cn/OutInterface/GetBurnList.ashx?pscode=%s&outputcode=&day=&SystemType=C16A882D480E678F&sgn=9038d4f536de5792ef481805c058a90a58817438&ts=1679630339213&tc=56076664'
        # 'https://ljgk.envsc.cn/OutInterface/GetBurnList.ashx?pscode=%s&outputcode=3255E390BCC698220F251F2F5AB40F30&day=20230323&SystemType=C16A882D480E678F&sgn=241563365ad7b6e5a319820df70ee2c4b51751d1&ts=1679636044133&tc=85172472'
        with open('naive_spider/data/fen_shao_lu.json') as f:
            self.ls = json.load(f)
        self.i = 198
    
    def start_requests(self):
        l = self.ls[self.i]
        yield scrapy.Request(self.url % l['ps_code'])

    def parse(self, response):
        details = json.loads(response.text)
        l = self.ls[self.i]
        print('=> processing %d:' % (self.i+1), l['ps_name'])
        for d in details:
            item = FenShaoLuItem()
            item['com_name'] = l['ps_name']
            item['com_address'] = l['address']
            item['province'] = l['fullregion_name'].split('-')[0]
            item['burn_ability'] = d['burn_ability']
            item['boiler_type'] = d['boiler_type']
            item['prod_date'] = d['creater_time']
            yield item
        
        self.i += 1
        time.sleep(20)
        l = self.ls[self.i]
        yield scrapy.Request(self.url % l['ps_code'])