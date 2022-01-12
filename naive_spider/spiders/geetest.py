from selenium import webdriver
import time
from datetime import datetime
import random
import os
from selenium.webdriver.chrome.options import Options
import requests

image_path = 'naive_spider/images/geetest'

def crawl():
    def download_img(driver):
        img = driver.find_element_by_class_name('geetest_item_img')
        src = img.get_attribute('src')
        if not src.startswith('http'):
            return False
        file_name = datetime.now().strftime('%Y_%m_%d_%H_%M_%S') + '.jpg'
        r = requests.get(src)
        with open(os.path.join(image_path, file_name), 'wb') as f:
            f.write(r.content)
        return True

    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-gpu')
    driver = webdriver.Chrome(chrome_options=chrome_options)
    driver.get('https://www.geetest.com/show')
    time.sleep(10)

    div = driver.find_element_by_class_name('tab-item-3')
    div.click()
    time.sleep(2)
    btn = driver.find_element_by_class_name('geetest_btn')
    btn.click()
    time.sleep(2)

    i = 0
    j = 0
    while True:
        res = True
        for c in range(10):
            res = download_img(driver)
            j += 1
            if res:
                i += 1
                refresh = driver.find_element_by_class_name('geetest_refresh')
                refresh.click()
                time.sleep(3)
            else:
                break
        if not res:
            btn = driver.find_element_by_class_name('geetest_reset_tip_content')
            btn.click()
            time.sleep(3)
        if i % 50 == 0:
            print('succ:', i)
        
        if j >= 150:
            break



