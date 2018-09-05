# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html


from pymongo import *

class JdBookMongoPipeline(object):
    def open_spider(self,spider):
        if spider.name == 'jd':
            client = MongoClient(host='127.0.0.1',port=27017)
            db = client.jd
            self.items = db.items

    def process_item(self, item, spider):
        if spider.name == 'jd':
            self.items.insert(dict(item))
        return item

class AmazonBookMongoPipeline(object):
    def open_spider(self,spider):
        if spider.name == 'amazon':
            client = MongoClient(host='127.0.0.1',port=27017)
            db = client.amazon
            self.items = db.items

    def process_item(self, item, spider):
        if spider.name == 'amazon':
            self.items.insert(dict(item))
        return item
