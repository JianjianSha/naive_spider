import requests
import random


url = 'http://xxxx'     # image url

def start(num=10):
    for i in range(num):
        download()
        if (i+1) % 10 == 0:
            print('finish:', i+1)

def download(save_dir='images/', ext='jpg'):
    resp = requests.get(url, stream=True)
    fname = random.randint(0, 100000)
    try:
        with open('%s/%06d.%s' % (save_dir, fname, ext), 'wb') as f:
            for chunk in resp:
                f.write(chunk)
    except Exception as e:
        print(e)