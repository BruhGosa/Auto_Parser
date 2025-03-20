import json
from tools.logger import logger

def save_to_json(car_data):
    try:
        logger.info("Сохранение данных в JSON файл")
        existing_data = []
        try:
            with open('auto_data.json', 'r', encoding='utf-8') as f:
                logger.info("Чтение существующего файла auto_data.json")
                existing_data = json.load(f)
                logger.info(f"Прочитано {len(existing_data)} записей из файла")
        except FileNotFoundError:
            logger.info("Файл auto_data.json не найден, будет создан новый")
        except json.JSONDecodeError:
            logger.warning("Ошибка декодирования JSON в файле auto_data.json, файл будет перезаписан")

        existing_data.extend(car_data)
        logger.info(f"Добавлено {len(car_data)} новых записей, всего: {len(existing_data)}")

        with open('auto_data.json', 'w', encoding='utf-8') as f:
            json.dump(existing_data, f, ensure_ascii=False, indent=2)
            logger.info("Данные успешно сохранены в auto_data.json")
            
    except Exception as e:
        logger.exception(f"Ошибка при сохранении данных: {e}")
        print(f"Ошибка при сохранении данных: {e}")
