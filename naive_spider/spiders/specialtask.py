from .imports import *


class ShanghaiCaptcha(scrapy.Spider):
    name = 'shanghaicaptcha'
    custom_settings = {
        'ITEM_PIPELINES': {}
    }
    def __init__(self, **kwargs):
        self.count = 2240
        self.url = 'http://222.66.64.156:8082/xxgs/CheckCodeImg2.jsp?d=%d'
        self.url = 'http://61.154.11.191/creditpub/captcha?preset=&ra=0.07100937359923254'
    

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


