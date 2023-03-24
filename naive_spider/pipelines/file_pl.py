import pandas as pd

class ExcelPipeline:
    def __init__(self):
        self.df = pd.DataFrame(columns=['com_name', 'com_address', 'province', 'boiler_type', 'burn_ability', 'prod_date'])
    def process_item(self, item, spider):
        series = pd.Series(item)
        self.df = self.df.append(series, ignore_index=True)
        return item

    def close_spider(self, spider):
        self.df.to_excel('naive_spider/data/FenShaoLu5.xlsx')