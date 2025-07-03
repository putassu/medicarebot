from faker import Faker
import pytz
from timezonefinder import TimezoneFinder
import geopy
import re
from db_handler.postgres_func import get_products_by_id
tzFinder = TimezoneFinder()


def get_random_person():
    # Создаем объект Faker с русской локализацией
    fake = Faker('ru_RU')

    # Генерируем случайные данные пользователя
    user = {
        'name': fake.name(),
        'address': fake.address(),
        'email': fake.email(),
        'phone_number': fake.phone_number(),
        'birth_date': fake.date_of_birth(),
        'company': fake.company(),
        'job': fake.job()
    }
    return user

import pytz

def get_msc_date(utc_time):
    # Задаем московский часовой пояс
    moscow_tz = pytz.timezone('Europe/Moscow')
    # Переводим время в московский часовой пояс
    moscow_time = utc_time.astimezone(moscow_tz)
    return moscow_time

def extract_number(text):
    match = re.search(r'\b(\d+)\b', text)
    if match:
        return int(match.group(1))
    else:
        return None

def extract_year(text):
    match = re.findall(r'\b19\d{2}\b|\b20\d{2}\b', text)
    if match:
        return int(match[0])
    else:
        return None

def extract_height(text):
    match = re.findall(r'\b[0-9]+[.,]{0,2}[0-9]*\b', text)
    if match:
        height = float(match[0].replace(',','.'))
        if height > 10 and height < 300:
            return height
        else:
            return 0
    else:
        return 0


def extract_cal(text):
    match = re.findall(r'\b[0-9]+[.,]{0,2}[0-9]*\b', text)
    if match:
        return float(match[0].replace(',','.'))
    else:
        return None

def calculate_nutrition_per_100g(items):
    # Инициализируем переменные для общей калорийности и БЖУ
    total_calories = 0
    total_proteins = 0
    total_fats = 0
    total_carbohydrates = 0
    total_mass = 0
    total_name = 'Продукт'

    # Проходим по каждому продукту в списке
    for item in items:
        # Получаем данные о калориях, БЖУ и массе продукта
        product_cal = item['product_cal']
        proteins = item['proteins']
        fats = item['fats']
        carbohydrates = item['carbohydrates']
        mass = item['mass']

        # Увеличиваем общие показатели с учетом массы продукта
        total_calories += product_cal * mass / 100
        total_proteins += proteins * mass / 100
        total_fats += fats * mass / 100
        total_carbohydrates += carbohydrates * mass / 100
        total_mass += mass
        total_name = item['product_name']

    # Рассчитываем показатели для блюда на 100 грамм
    if total_mass > 0:
        final_calories = total_calories / total_mass * 100
        final_proteins = total_proteins / total_mass * 100
        final_fats = total_fats / total_mass * 100
        final_carbohydrates = total_carbohydrates / total_mass * 100
        final_name = total_name

        # Возвращаем результаты в виде словаря
        return {
            "product_cal": round(final_calories, 2),
            "proteins": round(final_proteins, 2),
            "fats": round(final_fats, 2),
            "carbohydrates": round(final_carbohydrates, 2),
            "product_name":final_name
        }
    else:
        return None  # Если масса продуктов равна 0, возвращаем None



def get_timezone(city):
    geo = geopy.geocoders.Nominatim(user_agent="Admo_Bot")
    location = geo.geocode(city)
    if location:
        tz = tzFinder.timezone_at(lng=location.longitude, lat=location.latitude)
        print(f'TZ = {tz}')
        print(type(tz))
        return tz, location.address
    else:
        return None, None
{'products':
     [{'product_id': 33, 'measure': 'items', 'items': 3.0},
      {'product_id': 32, 'measure': 'grams', 'weight': 45.0},
      {'product_id': 31, 'measure': 'grams', 'weight': 50.0}],
 'photo_id': None, 'user_id': 462802644}


async def display_meal(data):
    report = []  # Список для формирования отчета
    total_calories = 0
    total_proteins = 0
    total_fats = 0
    total_carbohydrates = 0
    product_ids = [product.get('product_id') for product in data['products'] if product.get('product_id')]

    # Получаем продукты по идентификаторам
    products = await get_products_by_id(product_ids)

    for product_data in data['products']:
        # Если есть product_id, ищем продукт в полученном списке
        product_id = product_data.get('product_id')
        if product_id:
            # Получаем данные по продукту
            product = next((p for p in products if p.product_id == product_id), None)
            if not product:
                # Если продукт не найден, создаем запись с неизвестным продуктом
                product_name = "Неизвестный продукт"
                cal = product_data.get('cal', 0)  # Берем калории из data
                proteins = product_data.get('proteins', 0)
                fats = product_data.get('fats', 0)
                carbohydrates = product_data.get('carbohydrates', 0)
            else:
                # Если продукт найден в базе
                product_name = product.name
                cal = product.cal
                proteins = product.proteins or 0
                fats = product.fats or 0
                carbohydrates = product.carbohydrates or 0
        else:
            # Если product_id нет, продукт не из базы данных
            product_name = "Неизвестный продукт"
            cal = product_data.get('cal', 0)
            proteins = product_data.get('proteins', 0)
            fats = product_data.get('fats', 0)
            carbohydrates = product_data.get('carbohydrates', 0)

        # Обрабатываем данные для разных единиц измерения
        if product_data.get('measure') == 'grams':
            weight = product_data.get('weight', 0)
            total_cal = (cal / 100) * weight
            total_proteins_local = (proteins / 100) * weight if proteins else None
            total_fats_local = (fats / 100) * weight if fats else None
            total_carbohydrates_local = (carbohydrates / 100) * weight if carbohydrates else None
            description = f"{weight} грамм {product_name}"

        elif product_data.get('measure') == 'items':
            items = product_data.get('items', 0)
            weight_per_item = product.weight or 0  # Используем среднюю массу 1 продукта из базы, если есть
            total_weight = items * weight_per_item
            total_cal = (cal / 100) * total_weight
            total_proteins_local = (proteins / 100) * total_weight if proteins else None
            total_fats_local = (fats / 100) * total_weight if fats else None
            total_carbohydrates_local = (carbohydrates / 100) * total_weight if carbohydrates else None
            description = f"{items} штуки {product_name} ({total_weight} грамм)"

        else:
            # Если только калории, без веса или измерений
            total_cal = cal
            total_proteins_local = proteins
            total_fats_local = fats
            total_carbohydrates_local = carbohydrates
            description = f"{cal} ккал, БЖУ - {proteins}/{fats}/{carbohydrates}"

        # Формируем строку отчета
        bju_str = (
            f"{total_proteins_local:.1f}/{total_fats_local:.1f}/{total_carbohydrates_local:.1f}"
            if total_proteins_local is not None and total_fats_local is not None and total_carbohydrates_local is not None
            else "БЖУ у продукта не указано"
        )
        report.append(f"Вы съели: {description} - {total_cal:.1f} ккал, БЖУ - {bju_str}")

        # Добавляем к общим суммам
        total_calories += total_cal
        total_proteins += total_proteins_local or 0
        total_fats += total_fats_local or 0
        total_carbohydrates += total_carbohydrates_local or 0

    # Формируем итоговый отчет
    full_report = "\n".join(report)

    # Добавляем итоговые значения
    summary = (
        f"\n<b>Итого: {total_calories:.1f} ккал, "
        f"БЖУ - {total_proteins:.1f}/{total_fats:.1f}/{total_carbohydrates:.1f}</b>"
    )

    return full_report + summary

# geo = geopy.geocoders.Nominatim(user_agent="Admo_Bot")
# location = geo.geocode('ge3hthjjj')
# print(location.address)
# print(location.raw)

# tzFinder = TimezoneFinder()
# geo = geopy.geocoders.Nominatim(user_agent="Admo_Bot")
# location = geo.geocode(city)
# result = tzFinder.timezone_at(lng=location.longitude, lat=location.latitude)
# print(result)
