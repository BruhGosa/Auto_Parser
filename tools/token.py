import json
import re
import datetime
from tools.logger import logger
from tools.request import make_request_with_retry

# Глобальная переменная для хранения токена и времени его получения
token_info = {
    "token": None,
    "timestamp": None
}

def get_bearer_token(force_refresh=False):
    global token_info
    
    logger.info(f"Запрос токена. Принудительное обновление: {force_refresh}")
    
    # Проверяем, нужно ли обновить токен
    current_time = datetime.datetime.now()
    
    # Если токен существует и не требуется принудительное обновление, проверяем его срок действия
    if token_info["token"] and not force_refresh and token_info["timestamp"]:
        # Проверяем, прошло ли менее 23 часов с момента получения токена
        token_age = current_time - token_info["timestamp"]
        if token_age.total_seconds() < 23 * 3600: 
            logger.info("Используем существующий токен")
            print("Используем существующий токен")
            return token_info["token"]
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Origin': 'https://autospot.ru',
            'Referer': 'https://autospot.ru/'
        }
        
        logger.info("Получение главной страницы для извлечения токена")
        response = make_request_with_retry('https://autospot.ru/', headers=headers)
        if response and response.status_code == 200:
            logger.info("Главная страница успешно получена, ищем токен")
            # Ищем скрипт с id="serverApp-state"
            pattern = r'<script id="serverApp-state" type="application/json">(.*?)</script>'
            match = re.search(pattern, response.text)
            
            if match:
                logger.info("Найден скрипт serverApp-state, извлекаем данные")
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
                        token_info["token"] = access_token
                        token_info["timestamp"] = current_time
                        logger.info("Получен новый токен")
                        print("Получен новый токен")
                        return access_token
                    else:
                        logger.warning("Токен не найден в данных")
                else:
                    logger.warning(f"Ключ токена не найден или отсутствует 'body'. Найденный ключ: {token_key}")
            else:
                logger.warning("Скрипт serverApp-state не найден на странице")
            
        logger.error("Не удалось найти токен в serverApp-state")
        print("Не удалось найти токен в serverApp-state")
        return None
        
    except Exception as e:
        logger.exception(f"Ошибка при получении токена: {e}")
        print(f"Ошибка при получении токена: {e}")
        return None
