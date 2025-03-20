import json
import re
from lxml import html
from tools.logger import logger
from tools.request import make_request_with_retry
from tools.token import get_bearer_token
from tools.storage import save_to_json

def search_used_cars():
    logger.info("Запуск поиска подержанных автомобилей")
    page = 1
    max_page = 2
    while page <= max_page:
        logger.info(f"Обработка страницы {page} из {max_page}")
        # Проверяем, не нужно ли обновить токен
        bearer_token = get_bearer_token()
        
        if not bearer_token:
            logger.error("Не удалось получить токен для поиска подержанных автомобилей")
            return
        
        headers = {
            'Authorization': f'Bearer {bearer_token}',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Origin': 'https://autospot.ru',
            'Referer': 'https://autospot.ru/'
        }
        
        url = "https://autospot.ru/used-car/?sort=-views_count&limit=12&page="
        response = make_request_with_retry(url + str(page), headers=headers)

        if response and response.status_code == 200:
            logger.info(f"Страница {page} успешно получена, парсим данные")
            tree = html.fromstring(response.text)

            pagination_items = tree.xpath("//auto-pagination//ul/li")
            page_numbers = []
            for item in pagination_items:
                text = item.text_content().strip()
                if text.isdigit():
                    page_numbers.append(int(text))
            if page_numbers:
                max_page = max(page_numbers)
                logger.info(f"Обнаружено {max_page} страниц")
                print(max_page)
            
            cars_urls = tree.xpath("//auto-car-card/article/div/header/h3/a/@href")
            
            if not cars_urls:
                logger.warning(f"Данные не найдены на странице {page}")
                print("Данные не найдены на странице")
                break
                
            logger.info(f"Найдено {len(cars_urls)} автомобилей на странице {page}")
            for url in cars_urls:
                full_url = url
                logger.info(f"Обработка автомобиля: {full_url}")
                search_info_used_cars(full_url)
                
        else:
            logger.error(f"Не удалось получить страницу {page}")
                
        logger.info(f"Обработана страница {page}")
        print(f"Обработана страница {page}")
        page += 1

def search_info_used_cars(url):
    try:
        logger.info(f"Поиск основной информации по {url}")
        print("Поиск основной информации по " + url)
        response = make_request_with_retry(url)
        if response and response.status_code == 200:
            logger.info(f"Страница {url} успешно получена, извлекаем данные")
            # Получаем данные из JSON в скрипте
            pattern = r'<script id="serverApp-state" type="application/json">(.*?)</script>'
            match = re.search(pattern, response.text)
            car_data = {}
            characteristics = {}
            options = {}
            
            if match:
                logger.info("Найден скрипт serverApp-state, извлекаем JSON")
                data = json.loads(match.group(1))
                # Ищем ключ с информацией о машине
                car_key = next(
                    (key for key in data.keys() 
                    if 'api.autospot.ru/rest/v2/used-car/cars' in key),
                    None
                )
                if car_key:
                    logger.info("Найдены данные об автомобиле")
                    car_data = data[car_key].get('body', {})
                else:
                    logger.warning("Не найден ключ с информацией об автомобиле")
                
                # Получаем характеристики
                characteristics_key = next(
                    (key for key in data.keys() 
                    if 'api.autospot.ru/rest/car/all-characteristics' in key),
                    None
                )
                if characteristics_key:
                    logger.info("Найдены характеристики автомобиля")
                    characteristics = data[characteristics_key].get('body', {})
                else:
                    logger.warning("Не найден ключ с характеристиками автомобиля")
                
                # Получаем опции автомобиля
                options_key = next(
                    (key for key in data.keys() 
                    if 'api.autospot.ru/rest/used-car/options-two-column' in key),
                    None
                )
                
                options = []
                if options_key and 'body' in data[options_key] and 'columns' in data[options_key]['body']:
                    logger.info("Найдены опции автомобиля")
                    columns = data[options_key]['body']['columns']
                    for column in columns:
                        for group in column:
                            group_name = group.get('name', '')
                            if group_name and 'options' in group:
                                option_list = [option['name'] for option in group['options']]
                                options.append({
                                    'name': group_name,
                                    'list': option_list
                                })
                                logger.info(f"Добавлена группа опций: {group_name} с {len(option_list)} элементами")
                else:
                    logger.warning("Не найден ключ с опциями автомобиля или неверная структура")
            else:
                logger.warning("Не найден скрипт serverApp-state на странице")
            
            # Собираем фотографии
            logger.info("Извлечение фотографий автомобиля")
            tree = html.fromstring(response.text)
            photos = []
            all_photos = tree.xpath("//auto-gallery//img/@src | //auto-gallery-image//img/@src")
            for photo_url in all_photos:
                if "0x320" in photo_url:
                    clean_url = photo_url.split('?')[0]
                    if clean_url not in photos:
                        photos.append(clean_url)
            
            logger.info(f"Найдено {len(photos)} фотографий")
            
            car_data = [{
                    'url': url,
                    'brand': car_data.get('brand_name', None),
                    'model': car_data.get('model_name', None),
                    'generation': car_data.get('model_name', None),
                    'price': car_data.get('prices', {}).get('price', None),
                    'year': car_data.get('year', None),
                    'mileage': car_data.get('run', None),
                    'color': car_data.get('color_name', None),
                    'characteristics': characteristics,
                    'photos': photos,
                    'city': car_data.get('city_name', None),
                    'dealer': car_data.get('display_dealer_phone', None),
                    'options': options,
                }]
            
            logger.info(f"Сформированы данные для автомобиля: {car_data[0]['brand']} {car_data[0]['model']}")
            save_to_json(car_data)
            logger.info(f"Сохранены данные для машины: {url}")
            print(f"Сохранены данные для машины: {url}")
            
        else:
            logger.error(f"Не удалось получить страницу {url}, код ответа: {response.status_code if response else 'нет ответа'}")
            
    except Exception as e:
        logger.exception(f"Ошибка при получении данных ссылки {url}: {e}")
        print(f"Ошибка при получении данных ссылки {url}: {e}")


search_used_cars()