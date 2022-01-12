import scrapy
from ..utils.area import *
from pypinyin import pinyin
from ..basic.const import *
import json
from naive_spider.utils.config import DataSources
import chardet

from bs4 import BeautifulSoup
from .parser import *
from ..utils.tool import *
from scrapy_splash import SplashRequest
from ..items.generator import InvestApprove, InvestProject
from datetime import datetime
from urllib import request
from urllib import parse as urlparse
import time
import base64