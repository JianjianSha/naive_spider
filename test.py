# import naive_spider.spiders.geetest as geetest


# geetest.crawl()

import urllib.parse

def encode1(txt):
    return urllib.parse.quote(txt, encoding='GBK')


print(encode1('改造项目'))