# autospot.ru

Сбор данных с объявлений в autospot.ru
результат будет лежать в auto_data.json

## Расположение

- **Сервер**: IP сервера / Домен
- **Путь к проекту**: /.../.../.../parser

## Запуск

- Локально
    1. Клонировать репозиторий `git clone https://github.com/BruhGosa/Auto_Parser`
    2. Установить зависимости `pip install scrapy`
    3. Зайти в директорию `../autospot_scrapy`
    4. `scrapy crawl autospot`

## Модели/Структуры данных

### Объявление Б/У и Новых машин

```json
{
        "url": "",
        "brand": "",
        "model": "",
        "generation": "",
        "price": ,
        "year": ,
        "mileage": ,
        "color": "",
        "characteristics": [],
        "photos": [],
        "city": "",
        "dealer": "",
        "options": []
    }
```

## Основные зависимости

| Название      | Ссылка                                            |
| ------------- | ------------------------------------------------- |
| Scrapy        | [Ссылка](https://pypi.org/project/Scrapy/)        | 
