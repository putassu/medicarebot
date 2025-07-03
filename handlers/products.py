from aiogram import Router, F
from aiogram.filters import CommandStart, Command, CommandObject
from aiogram.types import Message
from keyboards.all_kb import main_kb, gender_kb
from keyboards.inline_kbs import (create_qst_inline_kb, get_login_tg,
                                  check_data, get_questionnaire, create_skip_button,
                                  create_yes_no_kb, get_new_meal_kb, get_products_inline_kb,
                                  get_new_product_kb)

create_skip_button()
from utils.utils import get_random_person, get_msc_date, extract_number, calculate_nutrition_per_100g
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from create_bot import questions
import asyncio
from aiogram.utils.chat_action import ChatActionSender
from create_bot import bot, admins
from aiogram.types import ReplyKeyboardRemove
from aiogram.fsm.state import State, StatesGroup
from utils.utils import extract_cal
from db_handler.postgres_func import get_profile, upsert_profile, upsert_product, get_product, delete_product, get_products
import re
from handlers.start import answer_products, goto_products

bot_id = 7307476763
class Product(StatesGroup):
    product_name = State()
    product_cal = State()
    proteins = State()
    fats = State()
    carbohydrates = State()
    photo_id = State()
    weight = State()
    is_favorite = State()
    check_state = State()
    product_calc = State()


product_router = Router()
product_router.message.filter(lambda message: message.photo or (message.text and not message.text.startswith('/')))
user_messages = {}

@product_router.callback_query(F.data == 'new_product')
async def start_product_process(call: CallbackQuery, state: FSMContext):
    await state.clear()
    async with ChatActionSender.typing(bot=bot, chat_id=call.message.chat.id):
        sent_message = await call.message.answer('Как называется продукт?')
    await call.answer('Введите название продукта')
    user_messages[call.message.from_user.id] = [sent_message.message_id]
    await state.set_state(Product.product_name)

@product_router.callback_query(F.data == 'new_product_calc')
async def start_product_process(call: CallbackQuery, state: FSMContext):
    await state.clear()
    async with ChatActionSender.typing(bot=bot, chat_id=call.message.chat.id):
        sent_message = await call.message.answer('Здесь нужно внести название блюда и ингредиенты с калорийностью, БЖУ и массой через запятую и бот сам рассчитает калорийность блюда. Название и ингредиенты на отдельной строчке. Пример ввода:\n'
                                                 '<b>Тыквенный суп</b>\n'
                                                 '<b>Тыква, 100.4, 6/2/20, 1000</b> <i>(Тыква, калорийность 100.4 ккал на 100 грамм, БЖУ 6/2/20, в блюде 1 кг тыквы)</i>\n'
                                                 '<b>Масло кунжутное, 800, 1/40/2, 50</b> <i>(Масло кунжутное, калорийность 800 ккал на 100 грамм, БЖУ 1/40/2, в блюде 50 г масла)</i>\n'
                                                 '<b>Картофель, 300, 5/4/40, 500</b> <i>(Картофель, калорийность 300 ккал на 100 грамм, БЖУ 5/4/40, в блюде 0.5 кг картошки)</i>\n')
    await call.answer('Введите название блюда и ингредиенты с КБЖУ')
    user_messages[call.message.from_user.id] = [sent_message.message_id]
    await state.set_state(Product.product_calc)


@product_router.message(F.text, Product.product_name)
async def start_product_process(message: Message, state: FSMContext):
    await state.update_data(product_name=message.text, user_id=message.from_user.id)
    async with ChatActionSender.typing(bot=bot, chat_id=message.chat.id):
        sent_message = await message.answer('Супер! А введи калорийность (ккал) на 100 г продукта: ')
    if message.from_user.id not in user_messages:
        user_messages[message.from_user.id] = []
    user_messages[message.from_user.id].append(sent_message.message_id)
    await state.set_state(Product.product_cal)

@product_router.message(F.text, Product.product_cal)
async def start_product_process(message: Message, state: FSMContext):
    cal = extract_cal(message.text)
    if not isinstance(cal, float):
        sent_message = await message.reply("Пожалуйста, введите калорийность корректно (ккал на 100 г продукта)")
        user_messages[message.from_user.id].append(sent_message.message_id)
        return
    await state.update_data(product_cal = cal)
    sent_message = await message.answer('Введите количество белков (в граммах) на 100 г продукта:',
                                        reply_markup=create_skip_button())
    if message.from_user.id not in user_messages:
        user_messages[message.from_user.id] = []
    user_messages[message.from_user.id].append(sent_message.message_id)
    await state.set_state(Product.proteins)

@product_router.callback_query(F.data=='skip_question', Product.proteins)
async def start_product_process(call: CallbackQuery, state: FSMContext):
    await state.update_data(proteins=0)
    sent_message = await call.message.answer('Введите количество жиров (в граммах) на 100 г продукта:',
                                             reply_markup=create_skip_button())
    if call.message.from_user.id not in user_messages:
        user_messages[call.message.from_user.id] = []
    user_messages[call.message.from_user.id].append(sent_message.message_id)
    await call.answer('Белков 0')
    await state.set_state(Product.fats)

@product_router.message(F.text, Product.proteins)
async def start_product_process(message: Message, state: FSMContext):
    proteins = extract_cal(message.text)
    if not isinstance(proteins, float):
        sent_message = await message.reply("Пожалуйста, введите количество белков в граммах")
        user_messages[message.from_user.id].append(sent_message.message_id)
        return
    await state.update_data(proteins = proteins)
    sent_message = await message.answer('Введите количество жиров (в граммах) на 100 г продукта:',
                                        reply_markup=create_skip_button())
    if message.from_user.id not in user_messages:
        user_messages[message.from_user.id] = []
    user_messages[message.from_user.id].append(sent_message.message_id)
    await state.set_state(Product.fats)

@product_router.callback_query(F.data=='skip_question', Product.fats)
async def start_product_process(call: CallbackQuery, state: FSMContext):
    await state.update_data(fats=0)
    sent_message = await call.message.answer('Введите количество углеводов (в граммах) на 100 г продукта:',
                                             reply_markup=create_skip_button())
    if call.message.from_user.id not in user_messages:
        user_messages[call.message.from_user.id] = []
    user_messages[call.message.from_user.id].append(sent_message.message_id)
    await call.answer('Жиров 0')
    await state.set_state(Product.carbohydrates)

@product_router.message(F.text, Product.fats)
async def start_product_process(message: Message, state: FSMContext):
    fats = extract_cal(message.text)
    if message.from_user.id not in user_messages:
        user_messages[message.from_user.id] = []
    if not isinstance(fats, float):
        sent_message =await message.reply("Пожалуйста, введите количество жиров в граммах")
        user_messages[message.from_user.id].append(sent_message.message_id)
        return
    await state.update_data(fats = fats)
    sent_message = await message.answer('Введите количество углеводов (в граммах) на 100 г продукта:', reply_markup=create_skip_button())
    user_messages[message.from_user.id].append(sent_message.message_id)
    await state.set_state(Product.carbohydrates)

@product_router.callback_query(F.data=='skip_question', Product.carbohydrates)
async def start_product_process(call: CallbackQuery, state: FSMContext):
    await state.update_data(carbohydrates=0)
    await call.answer('Углеводов 0')
    sent_message = await call.message.answer('Сколько грамм весит одна порция?', reply_markup=create_skip_button())
    if call.message.from_user.id not in user_messages:
        user_messages[call.message.from_user.id] = []
    user_messages[call.message.from_user.id].append(sent_message.message_id)
    await state.set_state(Product.weight)

@product_router.message(F.text, Product.carbohydrates)
async def start_product_process(message: Message, state: FSMContext):
    cb = extract_cal(message.text)
    if message.from_user.id not in user_messages:
        user_messages[message.from_user.id] = []
    if not isinstance(cb, float):
        sent_message = await message.reply("Пожалуйста, введите количество углеводов в граммах")
        user_messages[message.from_user.id].append(sent_message.message_id)
        return
    await state.update_data(carbohydrates = cb)
    sent_message = await message.answer('Сколько грамм весит одна порция?', reply_markup=create_skip_button())
    user_messages[message.from_user.id].append(sent_message.message_id)
    await state.set_state(Product.weight)

@product_router.callback_query(F.data=='skip_question', Product.weight)
async def start_product_process(call: CallbackQuery, state: FSMContext):
    await state.update_data(weight=None)
    await call.answer('У продукта отсутствует масса единицы')
    sent_message = await call.message.answer('Приложите фото', reply_markup=create_skip_button())
    if call.message.from_user.id not in user_messages:
        user_messages[call.message.from_user.id] = []
    user_messages[call.message.from_user.id].append(sent_message.message_id)
    await state.set_state(Product.photo_id)

@product_router.message(F.text, Product.weight)
async def start_product_process(message: Message, state: FSMContext):
    weight = extract_cal(message.text)
    if message.from_user.id not in user_messages:
        user_messages[message.from_user.id] = []
    if not isinstance(weight, float):
        sent_message = await message.reply("Пожалуйста, введите вес продукта в граммах")
        user_messages[message.from_user.id].append(sent_message.message_id)
        return
    await state.update_data(weight = weight)
    sent_message = await message.answer('Приложите фото продукта', reply_markup=create_skip_button())
    user_messages[message.from_user.id].append(sent_message.message_id)
    await state.set_state(Product.photo_id)

@product_router.callback_query(F.data=='skip_question', Product.photo_id)
async def start_product_process(call: CallbackQuery, state: FSMContext):
    await state.update_data(photo_id=None)
    data = await state.get_data()
    string = f'<b>{data.get('product_name')}</b>\n'
    string+=f'{data.get('product_cal')} ккал, БЖУ - {data.get('proteins')} / {data.get('fats')} / {data.get('carbohydrates')}'
    if data.get('weight'):
        string += f'1 единица продукта весит {data.get('weight')}'
    caption = f'Пожалуйста, проверьте все ли верно:\n{string}'
    sent_message = await call.message.answer(text=caption, reply_markup=check_data())
    if call.message.from_user.id not in user_messages:
        user_messages[call.message.from_user.id] = []
    user_messages[call.message.from_user.id].append(sent_message.message_id)
    await call.answer()
    await state.set_state(Product.check_state)

@product_router.message(F.photo, Product.photo_id)
async def start_questionnaire_process(message: Message, state: FSMContext):
    photo_id = message.photo[-1].file_id
    await state.update_data(photo_id=photo_id)
    data = await state.get_data()
    string = f'<b>{data.get('product_name')}</b>\n'
    string += f'{data.get('product_cal')} ккал, БЖУ - {data.get('proteins')} / {data.get('fats')} / {data.get('carbohydrates')}'
    if data.get('weight'):
        string += f'1 единица продукта весит {data.get('weight')}'
    caption = f'Пожалуйста, проверьте все ли верно:\n{string}'
    sent_message = await message.answer_photo(photo=data.get('photo_id'), caption=caption, reply_markup=check_data())
    if message.from_user.id not in user_messages:
        user_messages[message.from_user.id] = []
    user_messages[message.from_user.id].append(sent_message.message_id)
    await state.set_state(Product.check_state)


@product_router.message(F.document.mime_type.startswith('image/'), Product.photo_id)
async def start_questionnaire_process(message: Message, state: FSMContext):
    photo_id = message.document.file_id
    await state.update_data(photo_id=photo_id)
    data = await state.get_data()
    string = f'<b>{data.get('product_name')}</b>\n'
    string += f'{data.get('product_cal')} ккал, БЖУ - {data.get('proteins')} / {data.get('fats')} / {data.get('carbohydrates')}'
    if data.get('weight'):
        string += f'1 единица продукта весит {data.get('weight')}'
    caption = f'Пожалуйста, проверьте все ли верно:\n{string}'
    sent_message = await message.answer_photo(photo=data.get('photo_id'), caption=caption, reply_markup=check_data())
    if message.from_user.id not in user_messages:
        user_messages[message.from_user.id] = []
    user_messages[message.from_user.id].append(sent_message.message_id)
    await state.set_state(Product.check_state)


@product_router.message(F.document, Product.photo_id)
async def start_questionnaire_process(message: Message, state: FSMContext):
    sent_message = await message.answer('Пожалуйста, отправьте фото!', reply_markup=create_skip_button())
    if message.from_user.id not in user_messages:
        user_messages[message.from_user.id] = []
    user_messages[message.from_user.id].append(sent_message.message_id)
    await state.set_state(Product.photo_id)


# сохраняем данные
@product_router.callback_query(F.data == 'correct', Product.check_state)
async def start_questionnaire_process(call: CallbackQuery, state: FSMContext):
    await state.update_data(is_favorite=True)
    await state.update_data(user_id=call.from_user.id)
    data = await state.get_data()
    data['name'] = data.pop('product_name')
    data['cal'] = data.pop('product_cal')
    await upsert_product(**data)
    await call.answer('Новый продукт добавлен в ваш список!', show_alert=True)
    # await call.message.edit_reply_markup(reply_markup=None)
    # await call.message.delete()
    await goto_products(call, state)
    await delete_messages(call, state)
    await state.clear()

# запускаем анкету сначала
@product_router.callback_query(F.data == 'incorrect', Product.check_state)
async def start_questionnaire_process(call: CallbackQuery, state: FSMContext):
    await call.answer('Добавление нового продукта')
    await call.message.edit_reply_markup(reply_markup=None)
    await call.message.delete()
    await goto_products(call, state)
    await delete_messages(call, state)
    await state.clear()

@product_router.callback_query(F.data.startswith('view_product:'))
async def product_process(call: CallbackQuery):
    _, user_id, product_id, weight = call.data.split(':')
    product = await get_product(int(product_id))
    await call.answer()
    # await call.message.edit_reply_markup(reply_markup=None)
    # await call.message.delete()
    answer_text = (f'Ваш продукт - <b>{product.name}</b>, калорийность - <b>{round(product.cal,2)} ккал</b>,'
                   f' БЖУ - <b>{round(product.proteins,2)}/{round(product.fats,2)}/{round(product.carbohydrates,2)}</b>')
    if not product.photo_id:
        await call.message.answer(text=answer_text, reply_markup=get_new_meal_kb(product.product_id, weight))
    else:
        await call.message.answer_photo(photo=product.photo_id, caption=answer_text, reply_markup=get_new_meal_kb(product.product_id, weight))

@product_router.callback_query(F.data.startswith('product:delete:'))
async def start_questionnaire_process(call: CallbackQuery):
    _, _, product_id = call.data.split(':')
    await call.answer('Продукт удален')
    await delete_product(int(product_id))
    products = await get_products(call.message.from_user.id, 0)
    await call.message.edit_reply_markup(reply_markup=get_products_inline_kb(0, call.from_user.id, products))
    await call.message.delete()

@product_router.callback_query(F.data.startswith('product_pagination:'))
async def start_questionnaire_process(call: CallbackQuery):
    _, direction, user_id, page = call.data.split(':')
    products = await get_products(int(user_id), 0)
    await call.answer()
    await call.message.edit_reply_markup(reply_markup=get_products_inline_kb(int(page), int(user_id), products))
    # await call.message.delete()

@product_router.message(F.text, Product.product_calc)
async def start_questionnaire_process(message: Message, state: FSMContext):
    user_id = message.from_user.id
    products = [x.strip() for x in message.text.split('\n')]
    if len(products)<2:
        await message.answer(text=f'Ошибка в строке 1. Исправь и попробуй ещё раз')
        return
    product_name = products[0]
    items = []
    for idx, product in enumerate(products[1:]):
        product = re.findall(r'(.+),\s*(\d+|\d+\.\d+),\s*((\d+|\d+\.\d+)/(\d+|\d+\.\d+)/(\d+|\d+\.\d+)),\s*(\d+|\d+\.\d+)', product.strip())
        if product:
            if len(product[0]) == 7:
                name, cal, bju, b, j, u, mass = product[0]
                items.append({'product_name':product_name, 'product_cal':float(cal),
                              'proteins':float(b), 'fats':float(j), 'carbohydrates':float(u), 'mass':float(mass)})
            else:
                await message.answer(text=f'Ошибка в строке 1. Исправь и попробуй ещё раз')
                return
        else:
            await message.answer(text=f'Ошибка в строке {idx + 2}. Исправь и попробуй ещё раз')
            return
    await state.set_state(Product.weight)
    await state.update_data(**calculate_nutrition_per_100g(items))
    await message.answer('Сколько грамм весит одна порция?', reply_markup = create_skip_button())
    # await message.answer(text=f'Проверьте, всё ли верно: {calculate_nutrition_per_100g(items)}')

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
