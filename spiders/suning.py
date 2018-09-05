# -*- coding: utf-8 -*-
import scrapy
from scrapy.spiders import Spider
from book.items import BookItem
# from scrapy_redis.spiders import RedisSpider as Spider
import re
import json
import jsonpath

class SuningSpider(Spider):
    name = 'suning'
    allowed_domains = ['suning.com']
    start_urls = ['https://ipservice.suning.com/ipQuery.do']

    redis_key = "book:suning:start_url"

    def parse(self, response):
        ipQuery = json.loads(response.text)
        yield scrapy.Request(
            url='https://book.suning.com/',
            callback=self.parse_cat_list,
            meta={
                "ipQuery":ipQuery
            }
        )

    def parse_cat_list(self, response):

        #解析分类
        cat_1_titles = response.xpath('//div[@class="menu-item"]//h3/a/text()').extract()

        div_menu_sub_list = response.css('.menu-sub')

        for cat_1_title,div_menu_sub in zip(cat_1_titles,div_menu_sub_list):

            cat_2_titles = div_menu_sub.xpath('./div[@class="submenu-left"]/p/a/text()').extract()


            ul_list = div_menu_sub.xpath('./div[@class="submenu-left"]/ul')

            for index,ul in enumerate(ul_list):

                cat_2_title = '暂无分类'
                if index < len(cat_2_titles):
                    cat_2_title = cat_2_titles[index]

                cat_3_titles = ul.xpath('./li/a/text()').extract()
                cat_3_hrefs = ul.xpath('./li/a/@href').extract()

                for cat_3_title,cat_3_href in zip(cat_3_titles,cat_3_hrefs):
                    print(cat_1_title,"=>",cat_2_title,"=>",cat_3_title,"=>",cat_3_href)

                    # 请求列表页
                    yield scrapy.Request(
                        url=cat_3_href,
                        callback=self.parse_list_page,
                        meta=response.meta
                    )
            #         break
            #     break
            # break

        pass

    def parse_list_page(self,response):

        '''
        列表页分 上下两部分
        
        url => https://list.suning.com/emall/showProductList.do
        
        ci => 列表页面 url中的部分内容
        pg => 03
        cp => 页码 从  0 开始
        paging => 0 上 1 下
        '''
        # int(re.findall(r'共(.*?)页',response.text)[0])
        total_page = int(re.findall(r'param.pageNumbers = "(.*?)";',response.text)[0])

        ci = re.findall(r'-(.*?)-',response.url)[0]
        base_url = "https://list.suning.com/emall/showProductList.do?ci={}&cp={}&pg=03&paging={}"

        for cp in range(0,total_page+1,1):

            # 请求上半部分
            yield scrapy.Request(
                url=base_url.format(ci,cp,0),
                callback=self.parse_list_page_part,
                meta=response.meta
            )

            # 请求下半部分
            yield scrapy.Request(
                url=base_url.format(ci,cp,1),
                callback=self.parse_list_page_part,
                meta=response.meta
            )



        pass

    def parse_list_page_part(self,response):
        product_hrefs = response.xpath('//div[@class="img-block"]/a/@href').extract()

        for href in product_hrefs:
            yield scrapy.Request(
                url="https:" + href,
                callback=self.parse_detail,
                meta=response.meta
            )

        pass

    def parse_detail(self,response):

        ipQuery = response.meta["ipQuery"]

        html = response.text
        item = BookItem()
        item["name"] = response.xpath('//h1[@id="itemDisplayName"]/text()').extract_first().strip()

        # 价格是js渲染
        # 1. splash
        # 2. js逆向

        luaUrl = "https:" + re.findall(r'"luaUrl":"(.*?)"',html)[0]
        passPartNumber = re.findall(r'"passPartNumber":"(.*?)"',html)[0]
        partNumber =re.findall(r'"partNumber":"(.*?)"',html)[0]
        vendorCode = re.findall(r'"vendorCode":"(.*?)"',html)[0]
        provinceCode = ipQuery["provinceCommerceId"]
        lesCityId = ipQuery["cityLESId"]
        lesDistrictId = ipQuery["districtLESId"];
        a = lesCityId + lesDistrictId + "01"
        category1 = re.findall(r'"category1":"(.*?)"',html)[0]
        mdmCityId = ipQuery["cityMDMId"]
        cityId = ipQuery["cityCommerceId"]
        districtId = ipQuery["districtCommerceId"]
        cmmdtyType = re.findall(r'"cmmdtyType":"(.*?)"',html)[0]
        custLevel = ""
        mountType = re.findall(r'"mountType":"(.*?)"',html)[0]

        if mountType != "03":
            b = ""
        else:
            b = mountType

        catenIds = re.findall(r'"catenIds":"(.*?)"',html)[0]
        weight = re.findall(r'"weight":"(.*?)"',html)[0]
        e = ""


        price_url = luaUrl + "/nspcsale_0_" + passPartNumber + "_" + partNumber + "_" + vendorCode + "_" + provinceCode + "_" + lesCityId + "_" + a + "_" + category1 + "_" + mdmCityId + "_" + cityId + "_" + districtId + "_" + cmmdtyType + "_" + custLevel + "_" + b + "_" + catenIds + "_" + weight + "___" + e + ".html"

        yield  scrapy.Request(
            url=price_url,
            callback=self.parse_price,
            meta={
                "item":item
            }
        )

    def parse_price(self,response):

        item = response.meta["item"]

        result = json.loads(re.findall(r'pcData\((.*)\)',response.text,re.RegexFlag.DOTALL)[0])
        item["price"] = jsonpath.jsonpath(result,'$..netPrice')[0]
        print(item)
        # yield item

