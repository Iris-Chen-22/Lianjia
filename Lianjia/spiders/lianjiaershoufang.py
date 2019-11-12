# -*- coding: utf-8 -*-
import scrapy
import requests
import re
import time
from lxml import etree
from ..items import LianjiaItem
import random

class LianjiaSpider(scrapy.Spider):
    name = 'lianjiaspider'
    allowed_domains = ['sh.lianjia.com']

    def __init__(self,*args,**kwargs):
        self.headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Connection': 'keep-alive',
            'Cookie': 'lianjia_uuid=07e69a53-d612-4caa-9145-b31c2e9410f4; _smt_uid=5c2b6394.297c1ea9; UM_distinctid=168097cfb8db98-058790b6b3796c-10306653-13c680-168097cfb8e3fa; Hm_lvt_9152f8221cb6243a53c83b956842be8a=1546347413; _ga=GA1.2.1249021892.1546347415; _gid=GA1.2.1056168444.1546347415; all-lj=c60bf575348a3bc08fb27ee73be8c666; TY_SESSION_ID=d35d074b-f4ff-47fd-9e7e-8b9500e15a82; CNZZDATA1254525948=1386572736-1546352609-https%253A%252F%252Fbj.lianjia.com%252F%7C1546363071; CNZZDATA1255633284=2122128546-1546353480-https%253A%252F%252Fbj.lianjia.com%252F%7C1546364280; CNZZDATA1255604082=1577754458-1546353327-https%253A%252F%252Fbj.lianjia.com%252F%7C1546366122; lianjia_ssid=087352e7-de3c-4505-937e-8827e808c2ee; select_city=440700; Hm_lpvt_9152f8221cb6243a53c83b956842be8a=1546391853',
            'DNT': '1',
            'Host': 'sh.lianjia.com',
            'Referer': 'https://sh.lianjia.com/',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36'
        }
        self.start_urls = 'http://sh.lianjia.com/ershoufang/'
        super().__init__(*args, **kwargs)

    def start_requests(self):
        #包含yield语句的函数是一个生成器，每次产生一个值，函数被冻结，被唤醒后再次产生一个值
        yield scrapy.Request(url=self.start_urls, headers=self.headers, method='GET', callback=self.parse)
        #callback指定该请求返回的Response由哪个函数来处理

    def parse(self, response):
        lists = response.body.decode('utf-8')
        selector = etree.HTML(lists)
        #在进行网页抓取的时候，分析定位html节点
        #将文件读入，解析成树，然后根据路径定位到每个节点
        area_list = selector.xpath('/html/body/div[3]/div/div[1]/dl[2]/dd/div[1]/div/a')
        # etree.HTML得到的内容可以直接使用xpath
        for area in area_list:
            try:
                area_hanzi = area.xpath('text()').pop() #['浦东', '闵行', '宝山', '徐汇'...]
                area_pinyin = area.xpath('@href').pop().split('/')[2] #['/ershoufang/pudong/', '/ershoufang/minhang/', '/ershoufang/baoshan/'...]
                area_url = 'http://sh.lianjia.com/ershoufang/{}/'.format(area_pinyin)
                print(area_url)
                yield scrapy.Request(url=area_url, headers=self.headers, callback=self.detail_url, meta={"id1":area_hanzi, "id2":area_pinyin})
            except Exception:
                pass

    def get_latitude(self, url):  # 进入每个房源链接抓经纬度
        p = requests.get(url, headers=self.headers)
        time.sleep(3)
        regex = '''resblockPosition.(.+)'''
        items = re.search(regex, p.text).group(1)
        content = items.split(",")  # 经纬度
        longitude_latitude = ",".join(content[:2])
        return longitude_latitude


    def detail_url(self, response):
        for i in range(1,3): #获取1-100页
            url = 'http://sh.lianjia.com/ershoufang/{}/pg{}/'.format(response.meta["id2"], str(i))
            time.sleep(random.randint(1,5)) #随机等待1-5秒
            try:
                contents = requests.get(url, headers=self.headers)
                contents = etree.HTML(contents.content.decode('utf-8'))
                houselist = contents.xpath('//*[@id="content"]/div[1]/ul/li')
                for house in houselist:
                    try:
                        item = LianjiaItem()
                        item['title'] = house.xpath('./div[1]/div[1]/a/text()').pop()
                        item['community'] = house.xpath('./div[1]/div[2]/div/a[1]/text()').pop()
                        item['model'] = house.xpath('./div[1]/div[3]/div/text()').pop().split('|')[0]
                        item['area'] = house.xpath('./div[1]/div[3]/div/text()').pop().split('|')[1]
                        item['focus_num'] = house.xpath('./div[1]/div[4]/text()').pop().split('/')[0]
                        item['time'] = house.xpath('./div[1]/div[4]/text()').pop().split('/')[1]
                        item['price'] = house.xpath('./div[1]/div[6]/div[1]/span/text()').pop()
                        item['average_price'] = house.xpath('./div[1]/div[6]/div[2]/span/text()').pop()
                        item['link'] = house.xpath('./div[1]/div[1]/a/@href').pop()
                        item['city'] = response.meta["id1"]
                        self.url_detail = house.xpath('./div[1]/div[1]/a/@href').pop()
                        item['Latitude'] = self.get_latitude(self.url_detail)
                    except Exception as e:
                        print(e)
                    else:
                        yield item

            except Exception:
                pass