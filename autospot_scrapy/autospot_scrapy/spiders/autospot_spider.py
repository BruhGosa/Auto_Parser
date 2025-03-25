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
        # Начинаем с подержанных автомобилей
        yield Request(
            url=self.used_cars_url + "1",
            callback=self.parse_used_cars_list,
            meta={'needs_token': True, 'page': 1, 'max_page': 2}
        )
    
    def parse_used_cars_list(self, response):
        page = response.meta.get('page', 1)
        max_page = response.meta.get('max_page', 2)
        
        logger.info("Processing page %d of %d (used cars)", page, max_page)
        
        # Обновляем максимальное количество страниц
        pagination_items = response.xpath("//auto-pagination//ul/li")
        page_numbers = []
        for item in pagination_items:
            text = item.xpath("text()").get("").strip()
            if text.isdigit():
                page_numbers.append(int(text))
        
        if page_numbers:
            max_page = max(page_numbers)
            logger.info("Detected %d pages of used cars", max_page)
        
        # Получаем ссылки на автомобили
        cars_urls = response.xpath("//auto-car-card/article/div/header/h3/a/@href").getall()
        
        if not cars_urls:
            logger.warning("No data found on page %d (used cars)", page)
        else:
            logger.info("Found %d used cars on page %d", len(cars_urls), page)
            for url in cars_urls:
                full_url = response.urljoin(url)
                yield Request(
                    url=full_url,
                    callback=self.parse_used_car_info,
                    meta={'needs_token': False}
                )
        
        # Переходим на следующую страницу, если она есть
        if page < max_page:
            next_page = page + 1
            yield Request(
                url=self.used_cars_url + str(next_page),
                callback=self.parse_used_cars_list,
                meta={'needs_token': True, 'page': next_page, 'max_page': max_page}
            )
        elif page == max_page:
            # После обработки всех подержанных авто переходим к новым
            logger.info("Finished processing used cars, moving to new cars")
            yield Request(
                url=self.new_cars_url + "1",
                callback=self.parse_new_cars_list,
                meta={'needs_token': True, 'page': 1, 'max_page': 2}
            )
    
    def parse_new_cars_list(self, response):
        page = response.meta.get('page', 1)
        max_page = response.meta.get('max_page', 2)
        
        logger.info("Processing page %d of %d (new cars)", page, max_page)
        
        # Обновляем максимальное количество страниц
        pagination_items = response.xpath("//auto-pagination//ul/li")
        page_numbers = []
        for item in pagination_items:
            text = item.xpath("text()").get("").strip()
            if text.isdigit():
                page_numbers.append(int(text))
        
        if page_numbers:
            max_page = max(page_numbers)
            logger.info("Detected %d pages of new cars", max_page)
        
        # Получаем ссылки на автомобили
        cars_urls = response.xpath("//auto-car-card/article/div/header/h3/a/@href").getall()
        
        if not cars_urls:
            logger.warning("No data found on page %d (new cars)", page)
        else:
            logger.info("Found %d new cars on page %d", len(cars_urls), page)
            for url in cars_urls:
                full_url = response.urljoin(url)
                yield Request(
                    url=full_url,
                    callback=self.parse_new_car_info,
                    meta={'needs_token': False}
                )
        
        # Переходим на следующую страницу, если она есть
        if page < max_page:
            next_page = page + 1
            yield Request(
                url=self.new_cars_url + str(next_page),
                callback=self.parse_new_cars_list,
                meta={'needs_token': True, 'page': next_page, 'max_page': max_page}
            )
    
    def parse_used_car_info(self, response):
        logger.info("Processing used car: %s", response.url)
        
        # Извлекаем JSON из скрипта
        script_data = self._extract_script_data(response)
        if not script_data:
            logger.error("Failed to extract script data for %s", response.url)
            return
        
        # Извлекаем данные об автомобиле
        car_data = self._extract_used_car_data(script_data)
        characteristics = self._extract_characteristics(script_data)
        options = self._extract_used_car_options(script_data)
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
        
        # Извлекаем JSON из скрипта
        script_data = self._extract_script_data(response)
        if not script_data:
            logger.error("Failed to extract script data for %s", response.url)
            return
        
        # Извлекаем данные об автомобиле
        car_data = self._extract_new_car_data(script_data)
        price = self._extract_price_data(script_data)
        characteristics = self._extract_characteristics(script_data)
        options = self._extract_new_car_options(script_data)
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

    def _extract_used_car_data(self, script_data):
        car_key = next(
            (key for key in script_data.keys() 
            if 'api.autospot.ru/rest/v2/used-car/cars' in key),
            None
        )
        return script_data.get(car_key, {}).get('body', {}) if car_key else {}

    def _extract_new_car_data(self, script_data):
        car_key = next(
            (key for key in script_data.keys() 
            if 'api.autospot.ru/rest/car/base-info' in key),
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

    def _extract_used_car_options(self, script_data):
        options_key = next(
            (key for key in script_data.keys() 
            if 'api.autospot.ru/rest/used-car/options-two-column' in key),
            None
        )
        return self._process_options(script_data, options_key)

    def _extract_new_car_options(self, script_data):
        options_key = next(
            (key for key in script_data.keys() 
            if 'api.autospot.ru/rest/car/all-options-two-column' in key),
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
                clean_url = photo_url.split('?')[0]
                if clean_url not in photos:
                    photos.append(clean_url)
        return photos
