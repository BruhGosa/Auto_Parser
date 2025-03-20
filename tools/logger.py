import logging
import os

def setup_logger():
    if not os.path.exists('logs'):
        os.makedirs('logs')
        
    # Настройка логирования
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("logs/autospot_parser.log", encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

# Создаем логгер для использования во всем приложении
logger = setup_logger()
