#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import logging
from datetime import datetime
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from autospot_scrapy.spiders.autospot_spider import AutospotSpider

class AutospotCrawler:
    """Обертка для запуска и управления пауком Autospot"""
    
    def __init__(self, output_file=None, log_file=None, max_pages=None):
        """
        Инициализация обертки
        
        Args:
            output_file (str): Путь к файлу для сохранения результатов
            log_file (str): Путь к файлу для логов
            max_pages (int): Максимальное количество страниц для обработки
        """
        self.settings = get_project_settings()
        
        os.makedirs('logs', exist_ok=True)
        os.makedirs('data', exist_ok=True)
        
        current_time = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        
        if output_file:
            self.output_file = output_file
        else:
            self.output_file = f'data/{current_time}_autospot.json'
        
        if log_file:
            self.log_file = log_file
        else:
            self.log_file = f'logs/{current_time}_autospot.log'
        
        self.max_pages = max_pages
        
        self.setup_logging()
        
        self.process = CrawlerProcess(self.settings)
    
    def setup_logging(self):
        logging.basicConfig(
            filename=self.log_file,
            format='%(asctime)s [%(name)s] %(levelname)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S',
            level=logging.INFO
        )
        self.logger = logging.getLogger(__name__)
    
    def run(self):
        try:
            self.logger.info("Starting Autospot crawler")

            self.settings.set('FEEDS', {
                self.output_file: {
                    'format': 'json',
                    'encoding': 'utf-8',
                    'indent': 2,
                    'ensure_ascii': False
                }
            })
            
            self.process.crawl(
                AutospotSpider,
                max_pages=self.max_pages
            )
            self.process.start()
            
            self.logger.info("Crawler finished successfully")
            return True
        except Exception as e:
            self.logger.exception(f"Error running crawler: {e}")
            return False

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Run Autospot crawler')
    parser.add_argument('--output', '-o', help='Output file path')
    parser.add_argument('--log', '-l', help='Log file path')
    parser.add_argument('--max-pages', '-m', type=int, help='Maximum number of pages to process')
    
    args = parser.parse_args()
    
    crawler = AutospotCrawler(
        output_file=args.output,
        log_file=args.log,
        max_pages=args.max_pages
    )
    
    success = crawler.run()
    sys.exit(0 if success else 1) 