# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
import json
import logging
import os

logger = logging.getLogger(__name__)

class AutospotScrapyPipeline:
    def __init__(self):
        self.file_name = 'auto_data.json'
        self.items = []
        
    def open_spider(self, spider):
        try:
            # Пытаемся прочитать существующие данные
            if os.path.exists(self.file_name) and os.path.getsize(self.file_name) > 0:
                with open(self.file_name, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    # Проверяем, что файл содержит валидный JSON
                    if content and content[0] == '[' and content[-1] == ']':
                        self.items = json.loads(content)
                        logger.info("Read %d records from existing file", len(self.items))
                    else:
                        logger.warning("File exists but contains invalid JSON. Creating new one.")
                        self.items = []
            else:
                logger.info("Creating new file auto_data.json")
                self.items = []
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.warning("Error reading file: %s. Creating new one.", e)
            self.items = []
    
    def close_spider(self, spider):
        self._save_to_file()
        logger.info("Spider finished. Total %d records saved to %s", len(self.items), self.file_name)
    
    def process_item(self, item, spider):
        item_dict = ItemAdapter(item).asdict()
        
        # Проверяем, есть ли уже такой URL в сохраненных данных
        item_url = item_dict.get('url', '')
        existing_urls = [i.get('url', '') for i in self.items]
        
        if item_url and item_url in existing_urls:
            logger.info("Item with URL %s already exists, updating", item_url)
            index = existing_urls.index(item_url)
            self.items[index] = item_dict
        else:
            self.items.append(item_dict)
            logger.info("Added car: %s %s", item_dict.get('brand'), item_dict.get('model'))
        
        # Сохраняем после каждого элемента
        self._save_to_file()
        
        return item
    
    def _save_to_file(self):
        """Сохраняет данные в JSON-файл с красивым форматированием"""
        try:
            with open(self.file_name, 'w', encoding='utf-8') as f:
                json.dump(self.items, f, ensure_ascii=False, indent=2)
            logger.debug("Data saved to %s (%d records)", self.file_name, len(self.items))
        except Exception as e:
            logger.error("Error saving data: %s", e)
