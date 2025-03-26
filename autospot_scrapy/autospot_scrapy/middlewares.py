# Define here the models for your spider middleware
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/spider-middleware.html

from scrapy import signals
import logging
import json
import re
import datetime
import requests

logger = logging.getLogger(__name__)

class TokenMiddleware:
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
        if 'dont_process_token' in request.meta:
            return None
            
        if not request.meta.get('needs_token'):
            return None
            
        token = self.get_bearer_token(spider)
        if not token:
            logger.error("Failed to get token for request")
            return None
            
        request.headers['Authorization'] = f'Bearer {token}'
        logger.info("Added token to request: %s", request.url)
        return None
    
    def get_bearer_token(self, spider, force_refresh=False):
        current_time = datetime.datetime.now()
        
        if not force_refresh and self.token_info["token"] and self.token_info["timestamp"]:
            token_age = current_time - self.token_info["timestamp"]
            if token_age.total_seconds() < 23 * 3600:
                return self.token_info["token"]
        
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
            
            if response.status_code != 200:
                logger.error("Failed to get page for token extraction: %s", response.status_code)
                return None
                
            pattern = r'<script id="serverApp-state" type="application/json">(.*?)</script>'
            match = re.search(pattern, response.text)
            if not match:
                logger.warning("Script serverApp-state not found on page")
                return None
                
            data = json.loads(match.group(1))
            token_key = next(
                (key for key in data.keys() 
                if 'api.autospot.ru/rest/oauth2/token' in key),
                None
            )
            
            if not token_key or 'body' not in data[token_key]:
                logger.warning("Token key not found or 'body' missing")
                return None
                
            access_token = data[token_key]['body'].get('access_token')
            if not access_token:
                logger.warning("Token not found in data")
                return None
                
            self.token_info["token"] = access_token
            self.token_info["timestamp"] = current_time
            logger.info("Received new token")
            return access_token
                
        except Exception as e:
            logger.exception("Error getting token: %s", e)
            return None
