from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from autospot_scrapy.spiders.autospot_spider import AutospotSpider

if __name__ == "__main__":
    process = CrawlerProcess(get_project_settings())
    process.crawl(AutospotSpider)
    process.start()