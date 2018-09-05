# -*- coding: utf-8 -*-
import scrapy
from scrapy import Spider

from scrapy_splash.request import SplashRequest
import json
from pprint import pprint
from book.items import BookItem

from scrapy_redis.spiders import RedisSpider as Spider

class JdSpider(Spider):
    name = 'jd'
    allowed_domains = ['jd.com','3.cn']
    start_urls = ['https://book.jd.com/booksort.html']

    redis_key = "book:jd:start_url"

    def parse(self, response):
        # 获取一级分类地址
        cat_1_title_list = response.xpath('//div[@class="mc"]/dl/dt/a/text()').extract()

        # 获取二级分类地址
        dd_list = response.xpath('//div[@class="mc"]/dl/dd')

        for cat_1_title,dd in zip(cat_1_title_list,dd_list):
            cat_2_title_list = dd.xpath('.//a/text()').extract()
            cat_2_href_list = dd.xpath('.//a/@href').extract()
            for cat_2_title,cat_2_href in zip(cat_2_title_list,cat_2_href_list):
                print(cat_1_title,"=>",cat_2_title,"=>",cat_2_href)
                # 构建列表页面
                '''
                yield SplashRequest(
                    url="https:" + cat_2_href,
                    callback=self.parse_list_page,
                    meta={
                        "cat_1_title": cat_1_title,
                        "cat_2_title": cat_2_title
                    }
                )
                '''
                yield scrapy.Request(
                    url="https:"+cat_2_href,
                    callback=self.parse_list_page,
                    meta={
                        "cat_1_title":cat_1_title,
                        "cat_2_title":cat_2_title
                    }
                )

        pass

    def parse_list_page(self,response):
        li_list = response.xpath('//li[@class="gl-item"]')

        data_sku_price_list = []
        items = []
        for li in li_list:
            item = {}
            item["name"] = li.xpath('.//div[@class="p-name"]//em/text()').extract_first().strip()

            '''
            发现 浏览器中能够用xpath提取到
            但是 程序中提取不到
            js渲染后的结果造成
            
            解决思路:
            1. splash（最终备选方案）
            2. 进行分析
            
            '''

            data_sku = li.xpath('./div/@data-sku').extract_first()
            if data_sku is not None:
                skuIds = "J_" + str(data_sku)
                item["skuIds"] = skuIds
                data_sku_price_list.append(skuIds)
            items.append(item)

        price_url = ','.join(data_sku_price_list)
        price_url = "https://p.3.cn/prices/mgets?skuIds=" + price_url

        yield scrapy.Request(
            url=price_url,
            callback=self.parse_price,
            meta={
                "items":items
            }
        )

        next_url = response.xpath('//a[@class="pn-next"]/@href').extract_first()
        if next_url is not None:
            next_url = "https://list.jd.com" + next_url
            yield scrapy.Request(
                url=next_url,
                callback=self.parse_list_page
            )

        pass

    def parse_price(self,response):
        # 解析价格 获取 item 保存item
        '''
        [
            {
                "name":"xxxx",
                "skuIds":"J_12090377"
            },
            ...
        ]
        '''
        items = response.meta["items"]
        '''
        [
            {
                "id":"J_12090377",
                "op":'108.00',
                ...
            },
            ...
        ]
        '''

        result = json.loads(response.text)

        price_items_dict = {price_item["id"]:price_item for price_item in result}
        for item in items:
            if item.get("skuIds") is not None:
                price_dict = price_items_dict[item["skuIds"]]
                item["price"] = price_dict["op"]

                book = BookItem()
                book["name"] = item["name"]
                book["price"] = item["price"]
                yield book
        pass