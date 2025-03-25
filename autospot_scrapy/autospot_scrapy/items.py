# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class AutospotScrapyItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    pass

class AutospotCarItem(scrapy.Item):
    url = scrapy.Field()
    brand = scrapy.Field()
    model = scrapy.Field()
    generation = scrapy.Field()
    price = scrapy.Field()
    year = scrapy.Field()
    mileage = scrapy.Field()
    color = scrapy.Field()
    characteristics = scrapy.Field()
    photos = scrapy.Field()
    city = scrapy.Field()
    dealer = scrapy.Field()
    options = scrapy.Field()
