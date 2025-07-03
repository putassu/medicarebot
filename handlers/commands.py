from aiogram import Router, F
from aiogram.filters import CommandStart, Command, CommandObject
from aiogram.types import Message
from keyboards.all_kb import main_kb, gender_kb
from keyboards.inline_kbs import create_qst_inline_kb, get_questionnaire, get_products_inline_kb, get_new_product_kb, \
    get_pressure_kb, get_drugs_kb, get_drugs_inline_kb
from utils.utils import get_random_person, get_msc_date, extract_number
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from create_bot import questions
import asyncio
from aiogram.utils.chat_action import ChatActionSender
from create_bot import bot, admins
from aiogram.types import ReplyKeyboardRemove
from aiogram.fsm.state import State, StatesGroup
from db_handler.postgres_func import get_profile, upsert_profile, get_products, get_user_profile, get_pressures, \
    get_drugs_by_user
from handlers.meals import Meal
from handlers.pressure import Pressure
from handlers.products import Product
from handlers.drugs import Drug

from aiogram.enums import ParseMode
from html import escape

command_router = Router()
command_router.message.filter(lambda message: message.text and message.text.startswith('/'))

@command_router.message(CommandStart())
async def cmd_start(message: Message, command: CommandObject, state: FSMContext):
    await state.clear()
    command_args: str = command.args
    await message.answer(
            f'Привет! Добро пожаловать в твой личный дневник здоровья.❗️'
            f' Здесь можно считать калории, вести дневник здоровья и много всего другого.'
            f' Воспользуйся главным меню внизу или командным меню слева',
            reply_markup=main_kb(message.from_user.id), parse_mode=ParseMode.HTML)

@command_router.message(Command('/faq'))
async def cmd_start_2(message: Message):
    await message.answer('Ответы на частые вопросы:', reply_markup=create_qst_inline_kb(questions))

@command_router.message(Command('new_meal'))
async def start_product_process(message: Message, state: FSMContext):
    await state.clear()
    async with ChatActionSender.typing(bot=bot, chat_id=message.chat.id):
        products = await get_products(message.from_user.id, 0)
        sent_message = await message.answer('Выберите продукт из своего меню или введите значения К Б Ж У вручную'
                                            ' (например, 100 ккал, 20 г белка, 10 г жиров, 30 г углеводов запиываются так:'
                                            ' 100 20 10 30. Калории обязательно нужно указать, БЖУ необязательно)',
                                                 reply_markup=get_products_inline_kb(page=0, user_id=message.from_user.id, items=products))
    # await call.answer('Выберите продукт')
    # user_messages[message.from_user.id] = [sent_message.message_id]
    await state.set_state(Meal.product_id)

@command_router.message(Command('new_product'))
async def start_product_process(message: Message, state: FSMContext):
    await state.clear()
    async with ChatActionSender.typing(bot=bot, chat_id=message.chat.id):
        sent_message = await message.answer('Как называется продукт?')
    # await call.answer('Введите название продукта')
    # user_messages[message.from_user.id] = [sent_message.message_id]
    await state.set_state(Product.product_name)

@command_router.message(Command('new_pressure'))
async def cmd_new_pressure(message: Message, state: FSMContext):
    await state.clear()
    sent_message = await message.answer('Введите систолическое давление', reply_markup=None)
    # user_messages[message.from_user.id] = [sent_message.message_id]
    await state.update_data(user_id=message.from_user.id)
    await state.set_state(Pressure.systolic)

@command_router.message(Command('pressure_report'))
async def cmd_new_pressure(message: Message, state: FSMContext):
    # await state.clear()
    user_id = message.from_user.id
    pressures = await get_pressures(user_id)
    pressures = [f'{pressure.date} - {pressure.systolic}/{pressure.diastolic}, {pressure.pulse} {pressure.comment}' for pressure in pressures]
    sent_message = await message.answer(f'Ваши последние измерения давления:\n{"\n".join(pressures)}\n'
                                        f'Чтобы внести измерения за прошлые периоды, нажмите "Импорт измерений давления"',
                                        reply_markup=get_pressure_kb())
    # user_messages[message.from_user.id] = [sent_message.message_id]

# @command_router.message(Command('my_drugs'))
# async def cmd_new_drugs(message: Message, state: FSMContext):
#     # await state.clear()
#     user_id = message.from_user.id
#     # drugs = await get_drugs(user_id)
#     drugs = None
#     sent_message = await message.answer(f'Ваши лекарства сегодня:\n{"\n".join(drugs)}\n'
#                                         f'Чтобы заполнить пропуски приёмов за предыдущие дни, нажмите "Импорт лекарств"',
#                                         reply_markup=get_pressure_kb())

# @command_router.message(Command('new_drug'))
# async def cmd_new_drugs(message: Message, state: FSMContext):
#     # await state.clear()
#     user_id = message.from_user.id
#     # drugs = await get_drugs(user_id)
#     drugs = None
#     sent_message = await message.answer(f'Ваши лекарства сегодня:\n{"\n".join(drugs)}\n'
#                                         f'Чтобы заполнить пропуски приёмов за предыдущие дни, нажмите "Импорт лекарств"',
#                                         reply_markup=get_drugs_kb())
#     await state.set_state(Drug.manual)

@command_router.message(Command('my_products'))
async def answer_products(message: Message, state: FSMContext):
    await state.clear()
    user_id = message.from_user.id
    products = await get_products(user_id, 0)
    await message.answer(text='Здесь ваши продукты. Продукты можно листать кнопками <b>Вперёд ▶️</b> и <b>◀️ Назад</b>.'
                              ' Чтобы посмотреть информацию по продукту или добавить его в приём пищи, нужно кликнуть по кнопке с продуктом. '
                              'Чтобы добавить продукт, нужно нажать на кнопку <b>Новый продукт ➕</b>. Если вам неизвестна калорийность блюда,'
                              ' но известна калорийность его ингредиентов, можно воспользоваться опцией <b>Калькулятор калорийности по ингредиентам 🧮</b>')
    if products:
        await message.answer('<b>Мои продукты</b>',
                         reply_markup=get_products_inline_kb(0, user_id, products, max_items=6))
    else:
        await message.answer(text='У вас пока нет продуктов. Хотите внести?', reply_markup=get_new_product_kb())

@command_router.message(Command('my_drugs'))
async def cmd_new_pressure(message: Message, state: FSMContext):
    await state.clear()
    user_id = message.from_user.id
    items = await get_drugs_by_user(int(user_id))
    sent_message = await message.answer('Ваши лекарства', reply_markup=get_drugs_inline_kb(0, user_id, items))
    await state.update_data(user_id=message.from_user.id)
    await state.set_state(Drug.name)