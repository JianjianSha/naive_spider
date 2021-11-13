from naive_spider.items.generator import key_info
from ..basic.const import DEBUG
from .dba import *
from ..utils.tool import *

class InvestPipeline:
    def process_item(self, item, spider):
        r = insert_ms(item)
        if r == 1:
            cprint('success insert to db:', item.key_info(), color='lightcyan')
        if r == -1:     # duplicate key error
            r = update_ms(item)
            if r == 1:
                cprint('success update to db', item.key_info(), color='lightblue')
            elif r == -1:
                cprint("check if the items value is valid ", item.key_info(), color='yellow')
        return item