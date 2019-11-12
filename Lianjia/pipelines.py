# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html

import csv, os

class LianjiaPipeline(object):

    def process_item(self, item, spider):
        f = open(r'./lianjia.csv', 'a+', newline= '')
        write = csv.writer(f)
        write.writerow((item['title'], item['community'], item['model'], item['area'], \
        item['focus_num'], item['time'], item['price'], item['average_price'], item['link'], \
        item['Latitude'], item['city']))
        f.close()

        return item
