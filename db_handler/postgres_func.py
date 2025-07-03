from asyncpg.pgproto.pgproto import timedelta
from sqlalchemy import (create_engine, Column, BigInteger,
                        String, Integer, Text, Numeric, SmallInteger, Float, Boolean, ForeignKey, TIMESTAMP, func, TIME)
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.future import select
from decouple import config
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from sqlalchemy.future import select
from typing import List
import asyncio
from sqlalchemy.orm import relationship
from datetime import UTC, tzinfo
from sqlalchemy import desc
Base = declarative_base()


class Pressure(Base):
    __tablename__ = 'pressure'
    __table_args__ = {'schema': 'medicare'}  # Указываем схему medicare

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False)  # Идентификатор пользователя
    systolic = Column(Integer, nullable=False)  # Систолическое давление
    diastolic = Column(Integer, nullable=False)  # Диастолическое давление
    pulse = Column(Integer, nullable=False)  # Пульс
    date = Column(TIMESTAMP, server_default=func.current_timestamp(), nullable=False)  # Дата и время измерения
    comment = Column(Text, nullable=True)  # Комментарий пользователя

class Drug(Base):
    __tablename__ = 'drugs'
    __table_args__ = {'schema': 'medicare'}

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False)
    name = Column(String, nullable=False)
    measure = Column(String, nullable=True)
    dosage = Column(Float, nullable=True)
    admtime = Column(TIME, nullable=False)  # время ежедневного напоминания
    repeats = Column(String, nullable=True)
    datetime = Column(TIMESTAMP, server_default=func.current_timestamp(), nullable=False)

    # Один ко многим с DrugAdm
    drug_adms = relationship("DrugAdm", back_populates="drug", cascade="all, delete-orphan")


class DrugAdm(Base):
    __tablename__ = 'drug_adm'
    __table_args__ = {'schema': 'medicare'}

    id = Column(Integer, primary_key=True, autoincrement=True)
    drug_id = Column(Integer, ForeignKey('medicare.drugs.id'), nullable=False)
    datetime = Column(TIMESTAMP, server_default=func.current_timestamp(), nullable=False)

    # Обратная связь с Drug
    drug = relationship("Drug", back_populates="drug_adms")

class Profile(Base):
    __tablename__ = 'profiles'
    __table_args__ = {'schema': 'medicare'}

    user_id = Column(BigInteger, primary_key=True)
    full_name = Column(String, nullable=True)
    user_login = Column(String, nullable=False)
    gender = Column(String, nullable=True)
    age = Column(Integer, nullable=True)
    city = Column(Text, nullable=True)
    timezone = Column(String, nullable=True)
    height = Column(Numeric, nullable=True)
    weight = Column(Numeric, nullable=True)
    activity_level = Column(SmallInteger, nullable=True)

class Product(Base):
    __tablename__ = 'products'
    __table_args__ = {'schema': 'medicare'}  # Указываем схему medicare
    product_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, primary_key=True)  # Пользователь
    name = Column(String, nullable=False)  # Название продукта
    cal = Column(Float, nullable=True)  # Калории
    proteins = Column(Float, nullable=True)  # Белки
    fats = Column(Float, nullable=True)  # Жиры
    carbohydrates = Column(Float, nullable=True)  # Углеводы
    photo_id = Column(Text, nullable=True)  # Идентификатор фото
    is_favorite = Column(Boolean, nullable=False, default=False)
    weight = Column(Float, nullable=True)
    date = Column(TIMESTAMP, server_default=func.current_timestamp(), nullable=False)
    product_meals = relationship("ProductMeal", back_populates="product")


class Meal(Base):
    __tablename__ = 'meals'
    __table_args__ = {'schema': 'medicare'}

    meal_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False)  # Идентификатор пользователя
    date = Column(TIMESTAMP, server_default=func.current_timestamp(), nullable=False)  # Дата и время приема пищи
    photo_id = Column(Text, nullable=True)  # Фото, если оно было прикреплено
    product_meals = relationship("ProductMeal", back_populates="meal")
    def __repr__(self):
        return f"<Meal(meal_id={self.meal_id}, user_id={self.user_id}, date={self.date}, photo_id={self.photo_id})>"

class ProductMeal(Base):
    __tablename__ = 'product_meal'
    __table_args__ = {'schema': 'medicare'}

    product_meal_id = Column(Integer, primary_key=True, autoincrement=True)  # Добавляем serial для уникальности записей
    meal_id = Column(Integer, ForeignKey('medicare.meals.meal_id'), nullable=False)
    product_id = Column(Integer, ForeignKey('medicare.products.product_id'), nullable=False)
    weight = Column(Float, nullable=False)  # Масса съеденного продукта
    items = Column(Integer, nullable=True)  # Количество продуктов (штуки)
    meal = relationship("Meal", back_populates="product_meals")
    # Связь с таблицей Product
    product = relationship("Product", back_populates="product_meals")
# Настройка подключения к базе данных
DATABASE_URL = config('PG_LINK')
async_engine = create_async_engine(DATABASE_URL, future=True, echo=True)
AsyncSessionLocal = sessionmaker(async_engine, expire_on_commit=False, class_=AsyncSession)

# Функция для получения профиля по user_id
async def get_profile(user_id: int):
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Profile).where(Profile.user_id == user_id))
        profile = result.scalar_one_or_none()
        return profile

# Функция для Upsert профиля
# Функция для Upsert профиля
async def upsert_profile(
    user_id: int, user_login: str, gender: str, age: int,
    city: str, timezone: str, height: float, activity_level: int, full_name=None, weight=None
):
    async with AsyncSessionLocal() as session:
        async with session.begin():
            # Проверка на наличие существующего профиля
            profile = await session.execute(select(Profile).where(Profile.user_id == user_id))
            existing_profile = profile.scalar_one_or_none()

            if existing_profile:
                # Обновляем существующий профиль
                existing_profile.full_name = full_name
                existing_profile.user_login = user_login
                existing_profile.gender = gender
                existing_profile.age = age
                existing_profile.city = city
                existing_profile.timezone = timezone
                existing_profile.height = height
                existing_profile.weight = weight
                existing_profile.activity_level = activity_level
            else:
                # Создаем новый профиль
                new_profile = Profile(
                    user_id=user_id,
                    full_name=full_name,
                    user_login=user_login,
                    gender=gender,
                    age=age,
                    city=city,
                    timezone=timezone,
                    height=height,
                    weight=weight,
                    activity_level=activity_level
                )
                session.add(new_profile)

            # Коммит изменений
            await session.commit()


async def get_products(user_id: int, page):
    async with AsyncSessionLocal() as session:  # Используем сессию внутри функции
        query = text("""
            SELECT * from medicare.products where user_id = :user_id
            order by is_favorite desc, date desc
        """)
        result = await session.execute(query, {"user_id": user_id})
        rows = result.fetchall()
        return rows


async def get_products_by_id(product_ids: list):
    async with AsyncSessionLocal() as session:
        # Формируем запрос с условием, что product_id находится в списке product_ids
        query = select(Product).where(Product.product_id.in_(product_ids)).order_by(Product.is_favorite.desc(), Product.date.desc())
        result = await session.execute(query)
        # Извлекаем все строки
        rows = result.scalars().all()
        return rows

async def get_user_profile(user_id: int):
    async with AsyncSessionLocal() as session:  # Используем сессию внутри функции
        query = text("""
            SELECT 
    user_id, 
    full_name,
    gender, 
    extract(YEAR FROM current_timestamp) - age AS age, 
    user_login, 
    city, 
    timezone, 
    height, 
    weight,
    ROUND(AVG(systolic)::numeric, 0) || '/' || ROUND(AVG(diastolic)::numeric, 0) AS pressure, 
    ROUND(AVG(pulse)::numeric, 0) AS pulse, 
    ROUND(AVG(value)::numeric, 0) AS glucose, 
    description,
    CASE gender
        WHEN '👨‍🦱Мужчина' THEN ROUND(((88.362 + (13.397 * weight::numeric) + (4.799 * height::numeric) - (5.677 * (extract(YEAR FROM current_timestamp) - age))) * coef)::numeric, 0)
        WHEN '👩‍🦱Женщина' THEN ROUND(((447.593 + (9.247 * weight::numeric) + (3.098 * height::numeric) - (4.330 * (extract(YEAR FROM current_timestamp) - age))) * coef)::numeric, 0)
    END AS metabolism, 
    ROUND((weight::numeric / ((height::numeric / 100) * (height::numeric / 100)))::numeric, 2) AS BMI
FROM 
    medicare.profiles pf
LEFT JOIN 
    medicare.pressure pp USING(user_id)
LEFT JOIN 
    medicare.glucose gg USING(user_id)
LEFT JOIN 
    medicare.activity_level USING(activity_level)
WHERE 
    user_id = :user_id
GROUP BY 
    user_id, full_name, description, coef, weight, height, age;
        """)
        result = await session.execute(query, {"user_id": user_id})
        row = result.fetchone()
        return row

async def get_activity_levels_list():
    async with AsyncSessionLocal() as session:  # Используем сессию внутри функции
        query = text("""
            select activity_level, description from medicare.activity_level
            order by activity_level asc
        """)
        result = await session.execute(query)
        rows = result.fetchall()
        return rows

async def upsert_product(
    user_id: int, name: str, cal: float, proteins: float, fats: float, carbohydrates: float,
    photo_id: str, is_favorite: bool, weight=None
):
    async with AsyncSessionLocal() as session:
        async with session.begin():
            # Проверка на наличие существующего продукта
            product = await session.execute(select(Product).where(Product.user_id == user_id, Product.name == name))
            existing_product = product.scalar_one_or_none()

            if existing_product:
                # Обновляем существующий продукт
                existing_product.cal = cal
                existing_product.proteins = proteins
                existing_product.fats = fats
                existing_product.carbohydrates = carbohydrates
                existing_product.photo_id = photo_id
                existing_product.is_favorite = is_favorite
                existing_product.weight = weight
                existing_product.date = datetime.now(UTC).replace(tzinfo=None)
            else:
                # Создаем новый продукт
                new_product = Product(
                    user_id=user_id,
                    name=name,
                    cal=cal,
                    proteins=proteins,
                    fats=fats,
                    carbohydrates=carbohydrates,
                    photo_id=photo_id,
                    is_favorite=is_favorite,
                    weight = weight
                )
                session.add(new_product)

# Функция для получения продукта по product_id
async def get_product(product_id: int):
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Product).where(Product.product_id == product_id))
        product = result.scalar_one_or_none()
        return product

async def get_meal(meal_id: int):
    async with AsyncSessionLocal() as session:
        products = []
        meals_query = (
            select(Meal)
            .options(
                joinedload(Meal.product_meals).joinedload(ProductMeal.product))  # Загружаем продукты через ProductMeal
            .filter(Meal.meal_id == meal_id))
        result = await session.execute(meals_query)
        meal = result.unique().scalar_one_or_none()
        if not meal:
            return
        meal_calories, meal_proteins, meal_fats, meal_carbohydrates = 0, 0, 0, 0
        for product_meal in meal.product_meals:
            product = product_meal.product
            if product:
                # Расчет на основании веса или количества продуктов
                if product_meal.items is not None:  # Проверяем на None
                    factor = float(product_meal.items) * (float(product.weight) if product.weight else 0) / 100.0
                elif product_meal.weight is not None:
                    factor = float(product_meal.weight or 0) / 100.0  # Приводим к float, если None
                else:
                    factor = 1

                meal_calories += float(product.cal or 0) * factor
                # Приводим к float, если None
                meal_proteins += float(product.proteins or 0) * factor  # Приводим к float, если None
                meal_fats += float(product.fats or 0) * factor  # Приводим к float, если None
                meal_carbohydrates += float(product.carbohydrates or 0) * factor  # Приводим к float, если None

                products.append({'product_id':product.product_id, 'product_name':product.name,
                                 'product_cal':product.cal, 'product_proteins':product.proteins})

        # Добавляем данные о приеме пищи в отчет
        print({'meal_id': meal.meal_id, 'photo_id': meal.photo_id, 'date': meal.date, 'cal': meal_calories,
             'proteins': meal_proteins, 'fats': meal_fats,
             'carbohydrates': meal_carbohydrates})
        return {'meal_id': meal.meal_id, 'photo_id': meal.photo_id, 'date': meal.date, 'cal': meal_calories,
             'proteins': meal_proteins, 'fats': meal_fats,
             'carbohydrates': meal_carbohydrates}


async def delete_product(product_id: int):
    async with AsyncSessionLocal() as session:
        async with session.begin():
            # Получаем продукт по product_id
            product = await session.execute(select(Product).where(Product.product_id == product_id))
            existing_product = product.scalar_one_or_none()

            if existing_product:
                # Удаляем продукт
                await session.delete(existing_product)
                await session.commit()  # Фиксируем изменения
                return f"Продукт с ID {product_id} удален."
            else:
                return f"Продукт с ID {product_id} не найден."



# Функция добавления данных в БД

async def add_meal2db(data):
    async with AsyncSessionLocal() as session:
        # Создаем новый прием пищи
        new_meal = Meal(user_id=data['user_id'], photo_id=data.get('photo_id'))
        session.add(new_meal)
        await session.flush()  # Получаем meal_id

        # Обрабатываем продукты
        for product_data in data['products']:
            product_id = product_data.get('product_id')

            # Если продукт не указан, создаем новый с введенными КБЖУ
            if product_id is None:
                new_product = Product(
                    user_id=data['user_id'],
                    name='Продукт без имени',  # Указываем имя по умолчанию
                    cal=product_data.get('cal'),
                    proteins=product_data.get('proteins'),
                    fats=product_data.get('fats'),
                    carbohydrates=product_data.get('carbohydrates'),
                    is_favorite=False
                )
                session.add(new_product)
                await session.flush()  # Получаем новый product_id
                product_id = new_product.product_id

            # Связываем продукт с приемом пищи через промежуточную таблицу
            new_product_meal = ProductMeal(
                meal_id=new_meal.meal_id,
                product_id=product_id,
                weight=product_data.get('weight'),
                items=product_data.get('items', None)  # Может отсутствовать
            )
            session.add(new_product_meal)

        await session.commit()
        return new_meal.meal_id


from sqlalchemy import select
from sqlalchemy.orm import joinedload
from datetime import datetime
import pytz


# Функция для получения и отображения отчета по питанию
from datetime import datetime
import pytz
from decimal import Decimal


async def display_meal_report(user_id: int, start_date: datetime, end_date: datetime) -> dict:
    async with AsyncSessionLocal() as session:
        result_values = []
        # Получаем профиль пользователя для timezone и данных для расчета metabolism и protein_min
        user_profile = await session.execute(select(Profile).filter_by(user_id=user_id))
        profile = user_profile.scalar_one_or_none()

        if not profile:
            return {'display_string':'Профиль пользователя не найден', 'result_values':None}

        user_timezone = pytz.timezone(profile.timezone) if profile.timezone else pytz.UTC

        # Конвертация введенных дат в локальное время пользователя
        start_date_local = user_timezone.localize(start_date)
        end_date_local = user_timezone.localize(end_date)

        # Сохраняем локальное время как naive для запроса в БД
        start_date_naive = start_date_local.astimezone(pytz.UTC).replace(tzinfo=None)
        end_date_naive = end_date_local.astimezone(pytz.UTC).replace(tzinfo=None)

        print(f'!!!!!!!!!!!!{start_date_naive} !!!!!!!!!!!{start_date_local}')

        # Получаем приемы пищи за указанный период с использованием naive дат
        meals_query = (
            select(Meal)
            .options(
                joinedload(Meal.product_meals).joinedload(ProductMeal.product))  # Загружаем продукты через ProductMeal
            .filter(Meal.user_id == user_id)
            .filter(Meal.date >= start_date_naive)  # Используем naive дату
            .filter(Meal.date <= end_date_naive)
            .order_by(desc(Meal.date)) # Используем naive дату
        )
        result = await session.execute(meals_query)
        meals = result.unique().scalars().all()
        print('--------------------------------------------')
        print(meals)

        if not meals:
            return {"display_string":f"Приёмы пищи за указанный период не найдены.", "result_values":None}

        # Рассчитываем нормы по калориям и белкам
        metabolism = calculate_metabolism(profile)
        protein_min = float(profile.weight or 0) * 1.2  # Приводим к float, если None

        report_lines = []
        total_calories, total_proteins, total_fats, total_carbohydrates = 0, 0, 0, 0

        current_day = None
        day_totals = {
            "calories": 0,
            "proteins": 0,
            "fats": 0,
            "carbohydrates": 0,
        }

        for meal in meals:
            meal_time = meal.date.replace(tzinfo=UTC).astimezone(user_timezone)  # Преобразуем дату в локальное время пользователя
            if current_day is None or current_day != meal_time.date():
                if current_day:
                    # Завершаем предыдущий день
                    report_lines.append(format_day_totals(current_day, day_totals, metabolism, protein_min))
                # Начинаем новый день
                current_day = meal_time.date()
                day_totals = {
                    "calories": 0,
                    "proteins": 0,
                    "fats": 0,
                    "carbohydrates": 0,
                }

            # Рассчитываем калории и БЖУ для текущего приема пищи
            meal_calories, meal_proteins, meal_fats, meal_carbohydrates = 0, 0, 0, 0
            for product_meal in meal.product_meals:
                product = product_meal.product
                if product:
                    # Расчет на основании веса или количества продуктов
                    if product_meal.items is not None:  # Проверяем на None
                        factor = float(product_meal.items) * (float(product.weight) if product.weight else 0) / 100.0
                    elif product_meal.weight is not None:
                        factor = float(product_meal.weight or 0) / 100.0  # Приводим к float, если None
                    else:
                        factor = 1

                    meal_calories += float(product.cal or 0) * factor
                    # Приводим к float, если None
                    meal_proteins += float(product.proteins or 0) * factor  # Приводим к float, если None
                    meal_fats += float(product.fats or 0) * factor  # Приводим к float, если None
                    meal_carbohydrates += float(product.carbohydrates or 0) * factor  # Приводим к float, если None

            # Добавляем данные о приеме пищи в отчет
            report_lines.append(
                f"{meal_time.strftime('%d.%m.%Y %H:%M')} - {meal_calories:.0f} ккал, "
                f"БЖУ - {meal_proteins:.1f}/{meal_fats:.1f}/{meal_carbohydrates:.1f}"
            )

            result_values.append({'meal_id':meal.meal_id, 'photo_id':meal.photo_id, 'date':meal_time, 'cal':meal_calories,
                                  'proteins':meal_proteins, 'fats':meal_fats,
                                  'carbohydrates':meal_carbohydrates})

            # Обновляем дневные и общие итоги
            day_totals["calories"] += meal_calories
            day_totals["proteins"] += meal_proteins
            day_totals["fats"] += meal_fats
            day_totals["carbohydrates"] += meal_carbohydrates

        # Добавляем финальный день в отчет
        if current_day:
            report_lines.append(format_day_totals(current_day, day_totals, metabolism, protein_min))

        # Итоговый отчет
        # print(report_lines)
        print('--------------------------------------------')
        print({'display_string':"\n".join(report_lines), 'result_values':result_values})
        return {'display_string':"\n".join(report_lines), 'result_values':result_values}


# Вспомогательные функции
from decimal import Decimal


def calculate_metabolism(profile):
    weight = float(profile.weight) if isinstance(profile.weight, Decimal) else profile.weight
    height = float(profile.height) if isinstance(profile.height, Decimal) else profile.height

    if profile.gender == '👨‍🦱Мужчина':
        metabolism = round(88.362 + (13.397 * weight) + (4.799 * height) - (5.677 * (datetime.now().year - profile.age)))
    elif profile.gender == '👩‍🦱Женщина':
        metabolism = round(447.593 + (9.247 * weight) + (3.098 * height) - (4.330 * (datetime.now().year - profile.age)))
    else:
        raise ValueError('Неизвестный пол')

    return metabolism


def get_activity_coef(activity_level: int):
    """Функция для получения коэффициента активности на основе уровня активности."""
    activity_levels = {
        1: 1.2,  # Минимальная активность
        2: 1.375,  # Легкая активность
        3: 1.55,  # Средняя активность
        4: 1.725,  # Высокая активность
        5: 1.9  # Очень высокая активность
    }
    return activity_levels.get(activity_level, 1.2)  # Возвращаем коэффициент или минимальный по умолчанию


def format_day_totals(day, totals, metabolism, protein_min):
    """Функция для форматирования итогов по дню."""
    calorie_status = "в дефиците калорий" if totals["calories"] < metabolism else "в избытке калорий"
    protein_status = "в дефиците белка" if totals["proteins"] < protein_min else "в норме по белку"
    return (
        f"<b>Итого за {day.strftime('%d.%m.%Y')} - {totals['calories']:.0f} ккал ({calorie_status}), "
        f"БЖУ - {totals['proteins']:.1f}/{totals['fats']:.1f}/{totals['carbohydrates']:.1f} "
        f"(норма белка {protein_min:.1f}, вы {protein_status})</b>\n"
    )


async def add_pressure_measurement(
        user_id: int, systolic: int, diastolic: int, pulse: int, comment: str = None
):
    async with AsyncSessionLocal() as session:
        async with session.begin():  # Контекстный менеджер для явного управления транзакцией
            # Создаем объект для записи
            new_measurement = Pressure(
                user_id=user_id,
                systolic=systolic,
                diastolic=diastolic,
                pulse=pulse,
                comment=comment
            )

            # Добавляем объект в сессию
            session.add(new_measurement)

        # Коммит автоматически выполняется после завершения session.begin()

    # Возвращаем результат
    return new_measurement


async def get_pressures(user_id: int):
    async with AsyncSessionLocal() as session:  # Используем сессию внутри функции
        query = text("""select id, user_id, systolic, diastolic, pulse, comment, pressure.date AT TIME ZONE 'UTC' AT TIME ZONE timezone AS date from medicare.pressure
join medicare.profiles using(user_id)
where user_id = :user_id
order by pressure.date desc
limit 100
        """)
        result = await session.execute(query, {"user_id": user_id})
        row = result.fetchall()
        return row

async def insert_drug(user_id: int, name: str, admtime: str, measure: str = None, dosage: float = None, repeats: str = None):
    admtime = datetime.strptime(admtime, '%H:%M').time()
    async with AsyncSessionLocal() as session:
        async with session.begin():
            new_drug = Drug(
                user_id=user_id,
                name=name,
                measure=measure,
                dosage=dosage,
                admtime=admtime,
                repeats=repeats
            )
            session.add(new_drug)
        await session.commit()
        return new_drug

async def get_drugs_by_user(user_id: int):
    async with AsyncSessionLocal() as session:
        query = select(Drug).where(Drug.user_id == user_id)
        result = await session.execute(query)
        drugs = result.scalars().all()
        return drugs

async def insert_drug_adm(drug_id: int):
    async with AsyncSessionLocal() as session:
        new_adm = DrugAdm(drug_id=drug_id)
        session.add(new_adm)
        await session.commit()
# from datetime import datetime, timedelta
# print('---------------------')
# start_date = datetime.strptime('01.10.2024','%d.%m.%Y')
# end_date = datetime.strptime('06.10.2024','%d.%m.%Y')
# print(start_date)
#
# start_date = datetime.now() - timedelta(hours=200)
# end_date = datetime.now()
# print(start_date)
# asyncio.run(get_meal(4))