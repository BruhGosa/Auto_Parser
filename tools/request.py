import requests
import time
import random
from tools.logger import logger

def make_request_with_retry(url, headers=None, max_retries=float('inf'), initial_delay=1):
    retry_count = 0
    delay = initial_delay
    
    logger.info(f"Выполняется запрос к URL: {url}")
    
    while retry_count < max_retries:
        try:
            response = requests.get(url, headers=headers, timeout=30)
            logger.info(f"Получен ответ с кодом: {response.status_code}")
            
            if response.status_code != 504:
                return response
            
            retry_count += 1
            logger.warning(f"Получена ошибка 504. Повторная попытка {retry_count} через {delay} сек...")
            print(f"Получена ошибка 504. Повторная попытка {retry_count} через {delay} сек...")
            time.sleep(delay)
            # Увеличиваем задержку с каждой попыткой (экспоненциальная задержка с небольшим случайным фактором)
            delay = min(60, delay * 1.5 + random.uniform(0, 1))
            
        except requests.exceptions.RequestException as e:
            retry_count += 1
            logger.error(f"Ошибка соединения: {e}. Повторная попытка {retry_count} через {delay} сек...")
            print(f"Ошибка соединения: {e}. Повторная попытка {retry_count} через {delay} сек...")
            time.sleep(delay)
            delay = min(60, delay * 1.5 + random.uniform(0, 1))
    
    logger.critical("Превышено максимальное количество попыток запроса")
    return None
