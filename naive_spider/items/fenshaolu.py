from scrapy import Item, Field


class FenShaoLuItem(Item):

    com_name = Field()
    com_address = Field()
    province = Field()
    boiler_type = Field()
    burn_ability = Field()
    prod_date = Field()