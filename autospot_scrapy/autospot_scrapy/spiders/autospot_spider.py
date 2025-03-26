import scrapy
import json
import re
import logging
from scrapy.http import Request
from autospot_scrapy.items import AutospotCarItem

logger = logging.getLogger(__name__)

class AutospotSpider(scrapy.Spider):
    name = "autospot"
    allowed_domains = ["autospot.ru"]
    
    def __init__(self, *args, **kwargs):
        super(AutospotSpider, self).__init__(*args, **kwargs)
        self.used_cars_url = "https://autospot.ru/used-car/?sort=-views_count&limit=12&page="
        self.new_cars_url = "https://autospot.ru/filters/?sort=-percent_discount&limit=12&page="
    
    def start_requests(self):
        # Начинаем с первых страниц обоих типов авто
        yield Request(
            url=self.used_cars_url + "1",
            callback=self.parse_cars_list,
            meta={'needs_token': True, 'page': 1, 'car_type': 'used'}
        )
        
        yield Request(
            url=self.new_cars_url + "1",
            callback=self.parse_cars_list,
            meta={'needs_token': True, 'page': 1, 'car_type': 'new'}
        )
    
    def parse_cars_list(self, response):
        page = response.meta.get('page', 1)
        car_type = response.meta.get('car_type', 'new')
        max_page = self._get_max_page(response)
        logger.info("Detected %d pages of %s cars", max_page, car_type)
        
        # Обрабатываем текущую страницу
        yield from self._process_car_list(
            response=response,
            page=page,
            car_type=car_type,
            callback=self.parse_new_car_info if car_type == 'new' else self.parse_used_car_info
        )
        
        # Запускаем параллельный парсинг остальных страниц
        if page == 1:
            base_url = self.new_cars_url if car_type == 'new' else self.used_cars_url
            yield from self._schedule_pagination(
                base_url=base_url,
                max_page=max_page,
                callback=self.parse_cars_list,
                meta={'car_type': car_type}
            )
    
    def parse_used_car_info(self, response):
        logger.info("Processing used car: %s", response.url)
        
        script_data = self._extract_script_data(response)
        if not script_data:
            logger.error("Failed to extract script data for %s", response.url)
            return
        
        car_data = self._extract_car_data(script_data, car_type='used')
        characteristics = self._extract_characteristics(script_data)
        options = self._extract_car_options(script_data, car_type='used')
        photos = self._extract_photos(response)
        
        # Создаем элемент
        item = AutospotCarItem()
        item['url'] = response.url
        item['brand'] = car_data.get('brand_name')
        item['model'] = car_data.get('model_name')
        item['generation'] = car_data.get('model_name')
        item['price'] = car_data.get('prices', {}).get('price')
        item['year'] = car_data.get('year')
        item['mileage'] = car_data.get('run')
        item['color'] = car_data.get('color_name')
        item['characteristics'] = characteristics
        item['photos'] = photos
        item['city'] = car_data.get('city_name')
        item['dealer'] = car_data.get('display_dealer_phone')
        item['options'] = options
        
        yield item
    
    def parse_new_car_info(self, response):
        logger.info("Processing new car: %s", response.url)
        
        script_data = self._extract_script_data(response)
        if not script_data:
            logger.error("Failed to extract script data for %s", response.url)
            return
        
        car_data = self._extract_car_data(script_data, car_type='new')
        price = self._extract_price_data(script_data)
        characteristics = self._extract_characteristics(script_data)
        options = self._extract_car_options(script_data, car_type='new')
        dealers_list = self._extract_dealers(script_data)
        photos = self._extract_photos(response)
        
        # Создаем элемент
        item = AutospotCarItem()
        item['url'] = response.url
        item['brand'] = car_data.get('brand_name')
        item['model'] = car_data.get('model_name')
        item['generation'] = car_data.get('model_name')
        item['price'] = price.get('price')
        item['year'] = car_data.get('year')
        item['mileage'] = car_data.get('run')
        item['color'] = car_data.get('color_name')
        item['characteristics'] = characteristics
        item['photos'] = photos
        item['city'] = car_data.get('city_name')
        item['dealer'] = dealers_list
        item['options'] = options
        
        yield item
    
    def _extract_script_data(self, response):
        try:
            # Ищем скрипт с id="serverApp-state"
            script = response.xpath('//script[@id="serverApp-state"]/text()').get()
            if script:
                return json.loads(script)
            else:
                # Альтернативный способ через регулярное выражение
                pattern = r'<script id="serverApp-state" type="application/json">(.*?)</script>'
                match = re.search(pattern, response.text)
                if match:
                    return json.loads(match.group(1))
            
            logger.warning("Script serverApp-state not found on page %s", response.url)
            return None
        except Exception as e:
            logger.exception("Error extracting data from script: %s", e)
            return None

    def _extract_car_data(self, script_data, car_type='new'):
        """Извлекает основные данные об автомобиле"""
        api_path = 'api.autospot.ru/rest/v2/used-car/cars' if car_type == 'used' else 'api.autospot.ru/rest/car/base-info'
        car_key = next(
            (key for key in script_data.keys() 
            if api_path in key),
            None
        )
        return script_data.get(car_key, {}).get('body', {}) if car_key else {}

    def _extract_price_data(self, script_data):
        price_key = next(
            (key for key in script_data.keys() 
            if 'api.autospot.ru/rest/car/price-block' in key),
            None
        )
        if price_key and 'body' in script_data[price_key] and 'prices' in script_data[price_key]['body']:
            return script_data[price_key]['body']['prices']
        return {}

    def _extract_characteristics(self, script_data):
        characteristics_key = next(
            (key for key in script_data.keys() 
            if 'api.autospot.ru/rest/car/all-characteristics' in key),
            None
        )
        return script_data.get(characteristics_key, {}).get('body', {}) if characteristics_key else {}

    def _extract_car_options(self, script_data, car_type='new'):
        """Извлекает опции автомобиля"""
        api_path = 'api.autospot.ru/rest/used-car/options-two-column' if car_type == 'used' else 'api.autospot.ru/rest/car/all-options-two-column'
        options_key = next(
            (key for key in script_data.keys() 
            if api_path in key),
            None
        )
        return self._process_options(script_data, options_key)

    def _process_options(self, script_data, options_key):
        options = []
        if not options_key:
            return options
        
        if 'body' in script_data.get(options_key, {}) and 'columns' in script_data[options_key]['body']:
            columns = script_data[options_key]['body']['columns']
            for column in columns:
                for group in column:
                    group_name = group.get('name', '')
                    if group_name and 'options' in group:
                        option_list = [option['name'] for option in group['options']]
                        options.append({
                            'name': group_name,
                            'list': option_list
                        })
        return options

    def _extract_dealers(self, script_data):
        dealers_list = []
        dealer_key = next(
            (key for key in script_data.keys() 
            if 'api.autospot.ru/rest/dealer/direct-offer' in key),
            None
        )
        
        if dealer_key and 'body' in script_data[dealer_key] and 'items' in script_data[dealer_key]['body']:
            dealers = script_data[dealer_key]['body']['items']
            for dealer in dealers:
                dealer_info = {
                    'name_dealer': dealer.get('dealer_group_name'),
                    'phone_dealer': dealer.get('phone')
                }
                dealers_list.append(dealer_info)
        return dealers_list

    def _extract_photos(self, response):
        photos = []
        all_photos = response.xpath("//auto-gallery//img/@src | //auto-gallery-image//img/@src").getall()
        for photo_url in all_photos:
            if "0x320" in photo_url:
                # Заменяем 0x320 на 0x0 в URL
                clean_url = photo_url.split('?')[0].replace('0x320', '0x0')
                if clean_url not in photos:
                    photos.append(clean_url)
        return photos

    def _get_max_page(self, response):
        """Определяет максимальное количество страниц"""
        pagination_items = response.xpath("//auto-pagination//ul/li")
        page_numbers = []
        for item in pagination_items:
            text = item.xpath("text()").get("").strip()
            if text.isdigit():
                page_numbers.append(int(text))
        return max(page_numbers) if page_numbers else 1

    def _process_car_list(self, response, page, car_type, callback):
        """Обрабатывает список автомобилей на странице"""
        cars_urls = response.xpath("//auto-car-card/article/div/header/h3/a/@href").getall()
        
        if not cars_urls:
            logger.warning("No data found on page %d (%s cars)", page, car_type)
            return
        
        logger.info("Found %d %s cars on page %d", len(cars_urls), car_type, page)
        for url in cars_urls:
            yield Request(
                url=response.urljoin(url),
                callback=callback,
                meta={'needs_token': False}
            )

    def _schedule_pagination(self, base_url, max_page, callback, meta=None):
        """Запускает параллельный парсинг страниц"""
        meta = meta or {}
        meta.update({'needs_token': True})
        
        for page_num in range(2, max_page + 1):
            meta['page'] = page_num
            yield Request(
                url=base_url + str(page_num),
                callback=callback,
                meta=meta,
                dont_filter=True
            )
