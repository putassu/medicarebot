import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from decouple import config
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram.fsm.storage.redis import RedisStorage
from contextlib import asynccontextmanager
import asyncpg

storage = RedisStorage.from_url(config('REDIS_URL'))
user = config('PG_USER')
password = config('PG_PASSWORD')
host = config('PG_HOST')
database = config('PG_DATABASE')

# pg_db = PostgresHandler(config('PG_LINK')) # Пул объявляем на уровне модуля



scheduler = AsyncIOScheduler(timezone='Europe/Moscow')
admins = [int(admin_id) for admin_id in config('ADMINS').split(',')]

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
redis_url = config('REDIS_URL')
bot = Bot(token=config('TOKEN'), default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=storage)

questions = {
    1: {'qst': 'Как внести приём пищи', 'answer': 'Внести приём пиищ можно через команду /new_meal из меню слева или нажав на кнопку с продуктом из меню, который вы поели'},
    2: {'qst': 'Как внести пием пищи, если я не знаю его продуктовый состав, только калорийность?', 'answer': 'В этом случае просто нужно ввести КБЖУ через пробел, например, для блюда с КБЖУ 100 ккал, 23/34/30 строка ввода выглядит вот так "100 23 34 30"'},
    3: {'qst': 'Как посмотреть список моих продуктов?', 'answer': 'Список продуктов доступен через кнопку меню "Моё меню"'},
    4: {'qst': 'Как внести измерение давления?', 'answer': 'Новое измерение давление вносится через команду /new_pressure из командного меню слева'},
    5: {'qst': 'Как внести измерения давления за прошлые периоды?', 'answer': 'Для этого нужно сначала вызвать "Моё давление", а затем выбрать "Импорт измерений давления"'},
    6: {'qst': 'Как посмотреть сколько и чего я съел сегодня? За неделю? За месяц?', 'answer': 'Это можно посмотреть через соответвутствующие кнопки в "Дневнике питания"'},
    7: {'qst': 'Можно ли внести приемы пищи за прошлые периоды?', 'answer': 'В данный момент нет, но модуль находится в разработке'}
}