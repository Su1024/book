# -*- coding: utf-8 -*-
import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
from book.items import BookItem
from scrapy_redis.spiders import RedisCrawlSpider as CrawlSpider

class AmazonSpider(CrawlSpider):
    name = 'amazon'
    allowed_domains = ['amazon.cn']
    start_urls = ['https://www.amazon.cn/图书/b/ref=sa_menu_top_books_l1?ie=UTF8&node=658390051']

    redis_key = 'book:amazon:start_url'

    cat_1_le = LinkExtractor(
        restrict_xpaths=('//ul[@class="a-unordered-list a-nostyle a-vertical s-ref-indent-one"]//a[@class="a-link-normal s-ref-text-link"]')
    )

    cat_2_le = LinkExtractor(
        restrict_xpaths=('//ul[@class="a-unordered-list a-nostyle a-vertical s-ref-indent-two"]//a[@class="a-link-normal s-ref-text-link"]')
    )

    detail_le = LinkExtractor(
        restrict_xpaths=('//div[@class="a-column a-span12 a-text-center"]/a[@class="a-link-normal a-text-normal"]')
    )

    next_le = LinkExtractor(
        restrict_xpaths=('//a[@id="pagnNextLink"]')
    )

    rules = (
        Rule(cat_1_le, follow=True),
        Rule(cat_2_le, follow=True),
        Rule(next_le,follow=True),
        Rule(detail_le,follow=False,callback='parse_detail')
    )

    def parse_detail(self, response):
        item = BookItem()

        name = response.xpath('//span[@id="productTitle"]/text()').extract_first()
        if name is None:
            name = response.xpath('//span[@id="ebooksProductTitle"]/text()').extract_first()

        li_list = response.css('.swatchElement')
        price = ""
        for li in li_list:
            type = li.xpath('.//a/span/text()').extract_first()
            if type == '平装' or type == '精装':
                price =  li.xpath('.//a/span[2]/span/text()').extract_first()
                if price is not None:
                    price = price.strip().replace('￥',"")
                    break

        if name is not None and price is not None:
            item["name"] = name
            item["price"] = price
            yield item

