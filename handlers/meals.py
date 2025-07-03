from itertools import product
from datetime import datetime, timedelta
from aiogram import Router, F
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command, CommandObject
from aiogram.types import Message
from babel.messages.pofile import escape
from parso.python.tree import Param

from keyboards.all_kb import main_kb, gender_kb
from keyboards.inline_kbs import (create_qst_inline_kb, get_login_tg,
                                  check_data, get_questionnaire, create_skip_button,
                                  create_yes_no_kb, get_new_meal_kb, get_products_inline_kb,
                                  get_new_product_kb, create_add_product_button, get_meals_inline_kb)

create_skip_button()
from utils.utils import get_random_person, get_msc_date, extract_number, display_meal
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from create_bot import questions
import asyncio
from aiogram.utils.chat_action import ChatActionSender
from create_bot import bot, admins
from aiogram.types import ReplyKeyboardRemove
from aiogram.fsm.state import State, StatesGroup
from utils.utils import extract_cal, display_meal
from db_handler.postgres_func import (get_profile, upsert_profile, upsert_product,
                                      get_product, delete_product, get_products, add_meal2db,
                                      display_meal_report, get_meal)

bot_id = 7307476763
class Meal(StatesGroup):
    product_id = State()
    pfc = State()
    weight = State()
    items = State()
    add_more = State()
    photo_id = State()
    check_state = State()


meal_router = Router()
meal_router.message.filter(lambda message: message.photo or (message.text and not message.text.startswith('/')))
user_messages = {}
@meal_router.callback_query(F.data == 'new_meal')
async def start_product_process(call: CallbackQuery, state: FSMContext):
    await state.clear()
    async with ChatActionSender.typing(bot=bot, chat_id=call.message.chat.id):
        products = await get_products(call.from_user.id, 0)
        sent_message = await call.message.answer('Выберите продукт из своего меню или введите значения К Б Ж У вручную'
                                            ' (например, 100 ккал, 20 г белка, 10 г жиров, 30 г углеводов запиываются так:'
                                            ' 100 20 10 30. Калории обязательно нужно указать, БЖУ необязательно)',
                                                 reply_markup=get_products_inline_kb(page=0, user_id=call.from_user.id, items=products))
    await call.answer('Выберите продукт')
    user_messages[call.message.from_user.id] = [sent_message.message_id]
    await state.set_state(Meal.product_id)



@meal_router.callback_query(F.data == 'add_another_product', Meal.add_more)
async def start_product_process(call: CallbackQuery, state: FSMContext):
    async with ChatActionSender.typing(bot=bot, chat_id=call.message.chat.id):
        products = await get_products(call.from_user.id, 0)
        sent_message = await call.message.answer('Выберите следующий продукт из своего меню.',
                                                 reply_markup=get_products_inline_kb(page=0, user_id=call.from_user.id, items=products))
    await call.answer('Выберите следующий продукт')
    user_messages[call.message.from_user.id] = [sent_message.message_id]
    await state.set_state(Meal.product_id)


@meal_router.callback_query(F.data == 'finish_meal', Meal.add_more)
async def finish_meal(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    products = data.get('products', [])
    # await add_meal2db(products)
    await call.message.answer(text='Приложите фото', reply_markup=create_skip_button())
    await call.answer('Приложите фото')
    await state.set_state(Meal.photo_id)


@meal_router.callback_query(F.data.startswith('view_product:'), Meal.product_id)
async def start_product_process(call: CallbackQuery, state: FSMContext):
    _, user_id, product_id, weight = call.data.split(':')
    product_id = int(product_id)
    data = await state.get_data()
    await state.update_data(user_id=int(user_id))
    caption = f'Выбранный продукт: - {data}'
    if data.get('photo_id'):
        sent_message = await call.message.answer_photo(photo=data.get('photo_id'), caption=caption,
                                                       reply_markup=get_new_meal_kb(product_id, weight))
    else:
        sent_message = await call.message.answer(text=f'Выбранный продукт: - {data}', reply_markup=get_new_meal_kb(product_id, weight))
    user_messages[call.message.from_user.id] = [sent_message.message_id]
    await state.set_state(Meal.product_id)

@meal_router.message(F.text.regexp(r'\d+'), Meal.product_id)
async def start_product_process(message: Message, state: FSMContext):
    cal =[extract_number(x) for x in message.text.strip(' ').split(' ')]
    if len(cal)==1:
        sent_message = await message.answer(
            text=f'Вы поели на {cal[0]} ккал, БЖУ не указано',
            reply_markup=check_data())
        await state.update_data(products = [{'cal':float(cal[0])}], user_id=int(message.from_user.id))
    if len(cal)==4:
        sent_message = await message.answer(text=f'Вы поели на КБЖУ: - ккал={cal[0]}, белков={cal[1]}г, жиров={cal[2]}г, углеводов={cal[3]}г', reply_markup=check_data())
        await state.update_data(products = [{'cal':float(cal[0]), 'proteins':float(cal[1]), 'fats':float(cal[2]), 'carbohydrates':float(cal[3])}], user_id=int(message.from_user.id))
        user_messages[message.from_user.id] = [sent_message.message_id]
    await state.set_state(Meal.check_state)

@meal_router.callback_query(F.data.startswith('new_meal:'))
async def start_product_process(call: CallbackQuery, state: FSMContext):
    # await state.clear()
    _, measure, product_id, weight = call.data.split(':')
    product_id = int(product_id)
    data = await state.get_data()
    if 'products' not in data:
        data['products'] = []

        # Добавляем новый продукт в список
    data['products'].append({'product_id': int(product_id), 'measure':measure})

    # Обновляем состояние
    await state.update_data(products=data['products'])

    data = await get_product(int(product_id))


    if measure=='grams':
        sent_message = await call.message.answer('Введите массу съеденного продукта в граммах')
        await state.set_state(Meal.weight)
    if measure=='items':
        sent_message = await call.message.answer('Введите количество съеденного продукта в штуках')
        await state.set_state(Meal.items)
    await call.answer('Сколько продукта вы съели?')
    user_messages[call.message.from_user.id] = [sent_message.message_id]


@meal_router.message(F.text, Meal.weight)
async def start_meal_process(message: Message, state: FSMContext):
    weight = extract_cal(message.text)
    if message.from_user.id not in user_messages:
        user_messages[message.from_user.id] = []
    if not weight:
        sent_message = await message.reply("Пожалуйста, введите количество съеденного в граммах")
        user_messages[message.from_user.id].append(sent_message.message_id)
        return
    data = await state.get_data()
    products = data.get('products', [])
    products[-1]['weight'] = weight
    await state.update_data(products=products)

    sent_message = await message.answer(f'Вы съели {weight} грамм. Добавить ещё продукт или завершить прием пищи? ',
                                        reply_markup=create_add_product_button())
    user_messages[message.from_user.id].append(sent_message.message_id)
    await state.set_state(Meal.add_more)

@meal_router.message(F.text, Meal.items)
async def start_meal_process(message: Message, state: FSMContext):
    weight = extract_cal(message.text)
    if message.from_user.id not in user_messages:
        user_messages[message.from_user.id] = []
    if not weight:
        sent_message = await message.reply("Пожалуйста, введите количество съеденного в штуках")
        user_messages[message.from_user.id].append(sent_message.message_id)
        return
    data = await state.get_data()
    products = data.get('products', [])
    products[-1]['items'] = float(weight)
    await state.update_data(products=products)

    sent_message = await message.answer(f'Вы съели {weight} штук продукта. Добавить ещё продукт или завершить прием пищи? ',
                                        reply_markup=create_add_product_button())
    user_messages[message.from_user.id].append(sent_message.message_id)
    await state.set_state(Meal.add_more)

@meal_router.callback_query(F.data=='skip_question', Meal.photo_id)
async def start_product_process(call: CallbackQuery, state: FSMContext):
    await state.update_data(photo_id=None)
    await state.update_data(user_id=int(call.from_user.id))
    data = await state.get_data()
    caption = f'Пожалуйста, проверьте все ли верно:\n\n{await display_meal(data)}'
    sent_message = await call.message.answer(text=caption, reply_markup=check_data())
    if call.message.from_user.id not in user_messages:
        user_messages[call.message.from_user.id] = []
    user_messages[call.message.from_user.id].append(sent_message.message_id)
    await call.answer()
    await state.set_state(Meal.check_state)

@meal_router.message(F.photo, Meal.photo_id)
async def start_questionnaire_process(message: Message, state: FSMContext):
    photo_id = message.photo[-1].file_id
    await state.update_data(photo_id=photo_id)
    await state.update_data(user_id=int(message.from_user.id))
    data = await state.get_data()
    caption = f'Пожалуйста, проверьте все ли верно:\n\n {await display_meal(data)}'
    sent_message = await message.answer_photo(photo=data.get('photo_id'), caption=caption, reply_markup=check_data())
    # if message.from_user.id not in user_messages:
    #     user_messages[message.from_user.id] = []
    # user_messages[message.from_user.id].append(sent_message.message_id)
    await state.set_state(Meal.check_state)


@meal_router.message(F.document.mime_type.startswith('image/'), Meal.photo_id)
async def start_questionnaire_process(message: Message, state: FSMContext):
    photo_id = message.document.file_id
    await state.update_data(photo_id=photo_id)
    await state.update_data(user_id=int(message.from_user.id))
    data = await state.get_data()
    caption = f'Пожалуйста, проверьте все ли верно:\n\n {await display_meal(data)}'
    sent_message = await message.answer_photo(photo=data.get('photo_id'), caption=caption, reply_markup=check_data())
    # if message.from_user.id not in user_messages:
    #     user_messages[message.from_user.id] = []
    # user_messages[message.from_user.id].append(sent_message.message_id)
    await state.set_state(Meal.check_state)


@meal_router.message(F.document, Meal.photo_id)
async def start_questionnaire_process(message: Message, state: FSMContext):
    sent_message = await message.answer('Пожалуйста, отправьте фото!', reply_markup=create_skip_button())
    if message.from_user.id not in user_messages:
        user_messages[message.from_user.id] = []
    user_messages[message.from_user.id].append(sent_message.message_id)
    await state.set_state(Meal.photo_id)

@meal_router.callback_query(F.data == 'correct', Meal.check_state)
async def start_questionnaire_process(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    print(data)
    await add_meal2db(data)
    await call.answer('Новый приём пищи добавлен!', show_alert=True)
    await call.message.edit_reply_markup(reply_markup=None)
    await call.message.delete()
    await delete_messages(call, state)
    products = await get_products(call.from_user.id, 0)
    await call.message.answer('Выберите продукт из своего меню или введите значения К Б Ж У вручную'
                                            ' (например, 100 ккал, 20 г белка, 10 г жиров, 30 г углеводов запиываются так:'
                                            ' 100 20 10 30. Калории обязательно нужно указать, БЖУ необязательно)',
                              reply_markup=get_products_inline_kb(page=0, user_id=call.from_user.id, items=products))
    await state.clear()
    await state.set_state(Meal.product_id)
#
# запускаем анкету сначала
@meal_router.callback_query(F.data == 'incorrect', Meal.check_state)
async def start_questionnaire_process(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.answer('Выберите продукт')
    await delete_messages(call, state)
    async with ChatActionSender.typing(bot=bot, chat_id=call.message.chat.id):
        products = await get_products(call.from_user.id, 0)
        sent_message = await call.message.answer('Выберите продукт из своего меню или введите значения К Б Ж У вручную'
                                                 ' (например, 100 ккал, 20 г белка, 10 г жиров, 30 г углеводов запиываются так:'
                                                 ' 100 20 10 30. Калории обязательно нужно указать, БЖУ необязательно)',
                                                 reply_markup=get_products_inline_kb(page=0, user_id=call.from_user.id,
                                                                                     items=products))
    user_messages[call.message.from_user.id] = [sent_message.message_id]
    await state.set_state(Meal.product_id)

@meal_router.message(F.text=='🍵 Дневник питания')
async def start_meal_process(message: Message, state: FSMContext):
    user_id = message.from_user.id
    meals_dict = await display_meal_report(message.from_user.id, start_date=datetime.now() - timedelta(hours=24), end_date=datetime.now())
    # print('----------------------------')
    # print(meals_dict)
    # print(type(meals_dict))
    report = meals_dict.get('display_string')
    result =  meals_dict.get('result_values')
    if result:
        sent_message = await message.answer(f'<b>Отчёт за прошедшие 24 часа:</b>\n{report}',
                                            reply_markup=get_meals_inline_kb(0, user_id, sorted(result, key=lambda x: x['date'])))
    else:
        sent_message = await message.answer(f'За последние 24 часов не было приёмов пищи', reply_markup=get_meals_inline_kb(0, user_id, []))

@meal_router.callback_query(F.data=='meals:week')
async def start_meal_process(call:CallbackQuery, state: FSMContext):
    user_id = call.from_user.id
    meals_dict = await display_meal_report(call.from_user.id, start_date=datetime.now() - timedelta(days=7), end_date=datetime.now())
    await call.answer('Отчёт за неделю')
    # print('----------------------------')
    # print(meals_dict)
    # print(type(meals_dict))
    report = meals_dict.get('display_string')
    result =  meals_dict.get('result_values')
    if result:
        sent_message = await call.message.answer(f'<b>Отчёт за прошедшие 7 суток:</b>\n{report}',
                                            reply_markup=get_meals_inline_kb(0, user_id, sorted(result, key=lambda x: x['date'])))
    else:
        sent_message = await call.message.answer(f'{report}')

@meal_router.callback_query(F.data=='meals:month')
async def start_meal_process(call:CallbackQuery, state: FSMContext):
    user_id = call.from_user.id
    meals_dict = await display_meal_report(call.from_user.id, start_date=datetime.now() - timedelta(days=30), end_date=datetime.now())
    await call.answer('Отчёт за месяц')
    # print('----------------------------')
    # print(meals_dict)
    # print(type(meals_dict))
    report = meals_dict.get('display_string')
    result =  meals_dict.get('result_values')
    if result:
        sent_message = await call.message.answer(f'<b>Отчёт за прошедшие 30 дней:</b>\n{report}',
                                            reply_markup=get_meals_inline_kb(0, user_id, sorted(result, key=lambda x: x['date'])))
    else:
        sent_message = await call.message.answer(f'{report}')

@meal_router.callback_query(F.data.startswith('view_meal:'))
async def product_process(call: CallbackQuery):
    _, user_id, meal_id = call.data.split(':')
    meal = await get_meal(int(meal_id))
    await call.answer()
    # await call.message.edit_reply_markup(reply_markup=None)
    # await call.message.delete()
    if not meal.get('photo_id'):
        await call.message.answer(f'{meal}', reply_markup=None)
    else:
        await call.message.answer_photo(photo=meal.get('photo_id'), caption=f'{meal}', reply_markup=None)



async def delete_messages(message_or_callback, state: FSMContext):
    user_id = message_or_callback.from_user.id
    print(user_messages)

    if user_id in user_messages:
        for msg_id in user_messages[user_id]:
            try:
                # Проверка, что это обычное сообщение
                if isinstance(message_or_callback, Message):
                    await message_or_callback.bot.delete_message(message_or_callback.chat.id, msg_id)

                # Проверка, что это callback-запрос
                elif isinstance(message_or_callback, CallbackQuery):
                    await message_or_callback.bot.delete_message(message_or_callback.message.chat.id, msg_id)
                print(f'Удалил сообщение {msg_id}')
            except Exception as e:
                print(f"Не удалось удалить сообщение {msg_id}: {e}")

        # Очищаем список сообщений
        del user_messages[user_id]
    if bot_id in user_messages:
        for msg_id in user_messages[bot_id]:
            try:
                # Проверка, что это обычное сообщение
                if isinstance(message_or_callback, Message):
                    await message_or_callback.bot.delete_message(message_or_callback.chat.id, msg_id)

                # Проверка, что это callback-запрос
                elif isinstance(message_or_callback, CallbackQuery):
                    await message_or_callback.bot.delete_message(message_or_callback.message.chat.id, msg_id)
                print(f'Удалил сообщение {msg_id}')

            except Exception as e:
                print(f"Не удалось удалить сообщение {msg_id}: {e}")

        # Очищаем список сообщений
        del user_messages[bot_id]
