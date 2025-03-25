# Define here the models for your spider middleware
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/spider-middleware.html

from scrapy import signals

# useful for handling different item types with a single interface
from itemadapter import is_item, ItemAdapter

import logging
import json
import re
import datetime
from twisted.internet import defer
from twisted.internet.error import TimeoutError
from scrapy.http import HtmlResponse
from scrapy import Request
import random

logger = logging.getLogger(__name__)

class TokenMiddleware:
    # Глобальная переменная для хранения токена и времени его получения
    token_info = {
        "token": None,
        "timestamp": None
    }
    
    @classmethod
    def from_crawler(cls, crawler):
        middleware = cls()
        crawler.signals.connect(middleware.spider_opened, signal=signals.spider_opened)
        return middleware
    
    def spider_opened(self, spider):
        logger.info("TokenMiddleware initialized")
    
    def process_request(self, request, spider):
        # Пропускаем запросы для получения токена
        if 'dont_process_token' in request.meta:
            return None
            
        # Добавляем токен к запросу, если он нужен
        if 'needs_token' in request.meta and request.meta['needs_token']:
            token = self.get_bearer_token(spider)
            if token:
                request.headers['Authorization'] = f'Bearer {token}'
                logger.info("Added token to request: %s", request.url)
            else:
                logger.error("Failed to get token for request")
        
        return None
    
    def get_bearer_token(self, spider, force_refresh=False):
        logger.info("Token request. Force refresh: %s", force_refresh)
        
        # Проверяем, нужно ли обновить токен
        current_time = datetime.datetime.now()
        
        # Если токен существует и не требуется принудительное обновление, проверяем его срок действия
        if self.token_info["token"] and not force_refresh and self.token_info["timestamp"]:
            # Проверяем, прошло ли менее 23 часов с момента получения токена
            token_age = current_time - self.token_info["timestamp"]
            if token_age.total_seconds() < 23 * 3600:  # 23 часа в секундах
                logger.info("Using existing token")
                return self.token_info["token"]
        
        # Если токен нужно обновить, делаем запрос на главную страницу
        logger.info("Requesting new token")
        
        # Создаем новый запрос для получения токена
        request = Request(
            url='https://autospot.ru/',
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'application/json, text/plain, */*',
                'Origin': 'https://autospot.ru',
                'Referer': 'https://autospot.ru/'
            },
            meta={'dont_process_token': True}
        )
        
        # Выполняем запрос напрямую через requests
        import requests
        try:
            response = requests.get(
                'https://autospot.ru/',
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Accept': 'application/json, text/plain, */*',
                    'Origin': 'https://autospot.ru',
                    'Referer': 'https://autospot.ru/'
                },
                timeout=30
            )
            
            if response.status_code == 200:
                try:
                    # Ищем скрипт с id="serverApp-state"
                    pattern = r'<script id="serverApp-state" type="application/json">(.*?)</script>'
                    match = re.search(pattern, response.text)
                    
                    if match:
                        logger.info("Found serverApp-state script, extracting data")
                        data = json.loads(match.group(1))
                        # Ищем ключ с oauth2/token
                        token_key = next(
                            (key for key in data.keys() 
                            if 'api.autospot.ru/rest/oauth2/token' in key),
                            None
                        )
                        
                        if token_key and 'body' in data[token_key]:
                            access_token = data[token_key]['body'].get('access_token')
                            if access_token:
                                # Сохраняем токен и время его получения
                                self.token_info["token"] = access_token
                                self.token_info["timestamp"] = current_time
                                logger.info("Received new token")
                                return access_token
                            else:
                                logger.warning("Token not found in data")
                        else:
                            logger.warning("Token key not found or 'body' missing")
                    else:
                        logger.warning("Script serverApp-state not found on page")
                    
                    logger.error("Failed to find token in serverApp-state")
                    return None
                    
                except Exception as e:
                    logger.exception("Error getting token: %s", e)
                    return None
            else:
                logger.error("Failed to get page for token extraction: %s", response.status_code)
                return None
        except Exception as e:
            logger.exception("Error executing request: %s", e)
            return None

class RandomUserAgentMiddleware:
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0'
    ]
    
    def process_request(self, request, spider):
        request.headers['User-Agent'] = random.choice(self.user_agents)
        return None

class AutospotScrapySpiderMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the spider middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(self, response, spider):
        # Called for each response that goes through the spider
        # middleware and into the spider.

        # Should return None or raise an exception.
        return None

    def process_spider_output(self, response, result, spider):
        # Called with the results returned from the Spider, after
        # it has processed the response.

        # Must return an iterable of Request, or item objects.
        for i in result:
            yield i

    def process_spider_exception(self, response, exception, spider):
        # Called when a spider or process_spider_input() method
        # (from other spider middleware) raises an exception.

        # Should return either None or an iterable of Request or item objects.
        pass

    def process_start_requests(self, start_requests, spider):
        # Called with the start requests of the spider, and works
        # similarly to the process_spider_output() method, except
        # that it doesn't have a response associated.

        # Must return only requests (not items).
        for r in start_requests:
            yield r

    def spider_opened(self, spider):
        spider.logger.info("Spider opened: %s" % spider.name)


class AutospotScrapyDownloaderMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the downloader middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_request(self, request, spider):
        # Called for each request that goes through the downloader
        # middleware.

        # Must either:
        # - return None: continue processing this request
        # - or return a Response object
        # - or return a Request object
        # - or raise IgnoreRequest: process_exception() methods of
        #   installed downloader middleware will be called
        return None

    def process_response(self, request, response, spider):
        # Called with the response returned from the downloader.

        # Must either;
        # - return a Response object
        # - return a Request object
        # - or raise IgnoreRequest
        return response

    def process_exception(self, request, exception, spider):
        # Called when a download handler or a process_request()
        # (from other downloader middleware) raises an exception.

        # Must either:
        # - return None: continue processing this exception
        # - return a Response object: stops process_exception() chain
        # - return a Request object: stops process_exception() chain
        if isinstance(exception, TimeoutError):
            logger.warning("Timeout on request %s", request.url)
            return None
        return None

    def spider_opened(self, spider):
        spider.logger.info("Spider opened: %s" % spider.name)
