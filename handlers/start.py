from aiogram import Router, F
from aiogram.filters import CommandStart, Command, CommandObject
from aiogram.types import Message
from keyboards.all_kb import main_kb, gender_kb
from keyboards.inline_kbs import (create_qst_inline_kb, get_questionnaire, get_products_inline_kb,
                                  get_new_product_kb,get_pressure_kb, get_drugs_inline_kb)
from utils.utils import get_random_person, get_msc_date, extract_number
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from create_bot import questions
import asyncio
from aiogram.utils.chat_action import ChatActionSender
from create_bot import bot, admins
from aiogram.types import ReplyKeyboardRemove
from aiogram.fsm.state import State, StatesGroup
from db_handler.postgres_func import (get_profile, upsert_profile, get_products,
                                      get_user_profile, get_pressures, get_drugs_by_user)
from handlers.pressure import Pressure
from handlers.drugs import Drug


from aiogram.enums import ParseMode
from html import escape

start_router = Router()
start_router.message.filter(lambda message: message.photo or (message.text and not message.text.startswith('/')))


@start_router.message(F.text == '📖 О нас')
async def cmd_start_2(message: Message):
    await message.answer('Ответы на частые вопросы:', reply_markup=create_qst_inline_kb(questions))


@start_router.message(F.text == '🥬 Моё меню')
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


@start_router.callback_query(F.data == 'back_home')
async def back_home(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.answer(text='/start', reply_markup=main_kb(call.message.from_user.id))
    await call.answer('Переход на главное меню')

@start_router.callback_query(F.data.startswith('qst_'))
async def cmd_start(call: CallbackQuery):
    qst_id = int(call.data.replace('qst_', ''))
    qst_data = questions[qst_id]
    msg_text = f'Ответ на вопрос {qst_data.get("qst")}\n\n' \
               f'<b>{qst_data.get("answer")}</b>\n\n' \
               f'Выбери другой вопрос:'
    async with ChatActionSender(bot=bot, chat_id=call.from_user.id, action="typing"):
        await call.message.answer(msg_text, reply_markup=create_qst_inline_kb(questions))
        await call.answer()

@start_router.message(F.text == "🩺 Моё давление")
async def answer_pressure(message: Message, state: FSMContext):
    await state.clear()
    user_id = message.from_user.id
    pressures = await get_pressures(user_id)
    pressures = [f'{pressure.date.strftime("%d.%m.%Y %H:%M")} - {pressure.systolic}/{pressure.diastolic}, {pressure.pulse} {pressure.comment if pressure.comment else ""}' for
                 pressure in pressures]
    sent_message = await message.answer(f'Ваши последние измерения давления:\n{"\n".join(pressures)}')
    await message.answer(f'1. Внести давление, пульс и комментарий можно через запятую в формате - <b>120/80, 66, Чувствую себя хорошо</b>\n'
                         f'2. ...либо через кнопку <b>Внести измерение давления</b>\n'
                        f'3. Чтобы внести измерения за прошлые периоды, нажмите <b>Импорт измерений давления</b>', reply_markup=get_pressure_kb())
    await state.update_data(sent_message = sent_message.message_id)
    await state.set_state(Pressure.manual)

@start_router.message(F.text == '👤 Мой профиль')
async def start_questionnaire_process(message: Message, state: FSMContext):
    await state.clear()
    user_id = message.from_user.id
    async with ChatActionSender.typing(bot=bot, chat_id=message.chat.id):
        data = await get_user_profile(user_id)
        if data:
            caption = f'Ваш профиль: \n\n' \
                  f'<b>Полное имя</b>: {escape(data.full_name) if data.full_name else ' - '}\n' \
                  f'<b>Пол</b>: {data.gender if data.gender else ' - '}\n' \
                  f'<b>Возраст</b>: {data.age if data.age else ' - '} лет\n' \
                  f'<b>Логин в боте</b>: {escape(data.user_login) if data.user_login else ' - '}\n' \
                  f'<b>Город</b>: {escape(data.city) if data.city else ' - '}\n' \
                      f'<b>Уровень активности</b>: {data.description if data.description else ' - '}\n' \
                      f'<b>Мой текущий рост</b>: {data.height if data.height else ' - '}\n' \
                f'<b>Мой текущий вес</b>: {data.weight if data.weight else ' - '}\n' \
                      f'<b>Индекс массы тела</b>: {data.bmi if data.bmi else ' - '}\n' \
                      f'<b>Моё среднее давление</b>: {data.pressure if data.pressure else ' - '}\n' \
                f'<b>Мой средний пульс</b>: {data.pulse if data.pulse else ' - '}\n' \
                f'<b>Моя средняя глюкоза</b>: {data.glucose if data.glucose else ' - '}\n' \
                f'<b>Рассчетный суточный обмен</b>: {data.metabolism if data.metabolism else ' - '}'
            reply_markup = None
        else:
            caption = f'К сожалению, такого профиля не существует. Заполните, пожалуйста, анкету'
            reply_markup = get_questionnaire()

        await message.answer(text=caption, reply_markup=reply_markup, parse_mode=ParseMode.HTML)

# @start_router.message(F.text == '🥬 Моё меню')
async def goto_products(call: CallbackQuery, state: FSMContext):
    await state.clear()
    user_id = call.from_user.id
    products = await get_products(user_id, 0)
    await call.message.answer(text='Здесь ваши продукты. Продукты можно листать кнопками <b>Вперёд ▶️</b> и <b>◀️ Назад</b>.'
                              ' Чтобы посмотреть информацию по продукту или добавить его в приём пищи, нужно кликнуть по кнопке с продуктом. '
                              'Чтобы добавить продукт, нужно нажать на кнопку <b>Новый продукт ➕</b>. Если вам неизвестна калорийность блюда,'
                              ' но известна калорийность его ингредиентов, можно воспользоваться опцией <b>Калькулятор калорийности по ингредиентам 🧮</b>')
    if products:
        await call.message.answer('<b>Мои продукты</b>',
                         reply_markup=get_products_inline_kb(0, user_id, products, max_items=6))
    else:
        await call.message.answer(text='У вас пока нет продуктов. Хотите внести?', reply_markup=get_new_product_kb())

@start_router.message(F.text == '💊 Моя таблетница')
async def cmd_new_pressure(message: Message, state: FSMContext):
    await state.clear()
    user_id = message.from_user.id
    items = await get_drugs_by_user(int(user_id))
    print('!!!!!!!!!!')
    print('items')
    print(items)
    sent_message = await message.answer('Ваши лекарства', reply_markup=get_drugs_inline_kb(0, user_id, items))
    await state.update_data(user_id=message.from_user.id)
    await state.set_state(Drug.name)


