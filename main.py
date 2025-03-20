from tools.logger import logger
from parser.used_cars import search_used_cars
from parser.new_cars import search_new_cars

if __name__ == "__main__":
    logger.info("Запуск скрипта парсинга Autospot")
    try:
        #Поиск Б/У машин
        search_used_cars()
        #Поиск новых машин
        search_new_cars()
        logger.info("Скрипт успешно завершил работу")
    except Exception as e:
        logger.critical(f"Критическая ошибка при выполнении скрипта: {e}", exc_info=True)