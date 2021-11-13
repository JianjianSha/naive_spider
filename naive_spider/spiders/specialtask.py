from .imports import *


class ShanghaiCaptcha(scrapy.Spider):
    name = 'shanghaicaptcha'
    custom_settings = {
        'ITEM_PIPELINES': {}
    }
    def __init__(self, **kwargs):
        self.count = 2240
        self.url = 'http://222.66.64.156:8082/xxgs/CheckCodeImg2.jsp?d=%d'
    

    def _request(self):
        milisecond = int(round(time.time()*1000))
        url = self.url % milisecond
        return scrapy.Request(url)

    def start_requests(self):
        yield self._request()

    def parse(self, response):
        img = response.body
        filename = response.url.split('=')[1]
        
        with open('naive_spider/images/%s.jpg' % filename, 'wb') as f:
            f.write(img)
            self.count += 1
            print('=> %d, filename: %s' % (self.count, filename))
        if self.count < 5000:
            time.sleep(1)
            yield self._request()