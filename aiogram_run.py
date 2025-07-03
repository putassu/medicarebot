import asyncio
import asyncpg
from create_bot import bot, dp, scheduler
from handlers.commands import command_router
from handlers.drugs import drug_router
from handlers.start import start_router
from handlers.questionnaire import questionnaire_router
from handlers.products import product_router
from handlers.meals import meal_router
from handlers.pressure import pressure_router
from decouple import config
# from work_time.time_func import send_time_msg
from aiogram.types import BotCommand, BotCommandScopeDefault, Update
from aiogram.dispatcher.event.bases import UNHANDLED
from db_handler.postgres_func import get_profile
import logging
from aiogram import Dispatcher
import logging

# Настройка базового конфигурации логгера
logging.basicConfig(
    level=logging.DEBUG,  # Уровень логирования, можно изменить на DEBUG
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)

# Получаем логгер
logger = logging.getLogger(__name__)

from aiogram import types
from aiogram import BaseMiddleware


class LoggingMiddleware(BaseMiddleware):
    async def __call__(self, handler, event: Update, data: dict):
        # Логгирование содержимого события
        user_id = None

        if isinstance(event, types.Message):
            user_id = event.from_user.id
            logger.info(f"Message from {user_id}: {event.text}")
        elif isinstance(event, types.CallbackQuery):
            user_id = event.from_user.id
            logger.info(f"CallbackQuery from {user_id}: {event.data}")
        elif isinstance(event, types.InlineQuery):
            user_id = event.from_user.id
            logger.info(f"InlineQuery from {user_id}: {event.query}")
        elif hasattr(event, 'from_user'):
            user_id = event.from_user.id

        # Передаем управление дальше
        result = await handler(event, data)

        # Если событие не было обработано
        if result == UNHANDLED:
            logger.warning(f"Event from {user_id} was not handled: {event}")

        return result


async def set_commands():
    commands = [BotCommand(command='/start', description='Старт'),
                BotCommand(command='/start_2', description='Старт 2'),
                BotCommand(command='/faq', description='Справочная информация'),
                BotCommand(command='/new_pressure', description='Ввести показатели артериального давления'),
                BotCommand(command='/pressure_report', description='Отчёт по артериальному давлению'),
                BotCommand(command='/my_meal', description='Посмотреть приёмы пищи')]
    await bot.set_my_commands(commands)

async def main():
    # scheduler.add_job(send_time_msg, 'interval', seconds=10)
    # scheduler.start()
    dp.include_router(command_router)
    dp.include_router(start_router)
    dp.include_router(questionnaire_router)
    dp.include_router(product_router)
    dp.include_router(meal_router)
    dp.include_router(pressure_router)
    dp.include_router(drug_router)
    dp.update.middleware(LoggingMiddleware())
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)
    await set_commands()

if __name__ == "__main__":
    asyncio.run(main())