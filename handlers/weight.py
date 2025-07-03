from aiogram import Router, F
from aiogram.filters import CommandStart, Command, CommandObject
from aiogram.types import Message
from keyboards.all_kb import main_kb, gender_kb
from keyboards.inline_kbs import (create_qst_inline_kb, get_login_tg,
                                  check_data, get_questionnaire, create_skip_button,
                                  create_yes_no_kb, get_new_meal_kb, get_products_inline_kb,
                                  get_new_product_kb, create_add_product_button, get_pressure_kb)

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
from db_handler.postgres_func import (get_profile, upsert_profile, upsert_product,
                                      get_product, delete_product, get_products,
                                      add_pressure_measurement, get_pressures)
from datetime import datetime
import re

bot_id = 7307476763
class Weight(StatesGroup):
    manual = State()
    weight = State()
    comment = State()
    check_state = State()
    import_weight = State()
#     items = State()
#     add_more = State()
#     photo_id = State()
#     check_state = State()

weight_router = Router()
user_messages = {}
weight_router.message.filter(lambda message: message.photo or (message.text and not message.text.startswith('/')))

@weight_router.callback_query(F.data == 'new_weight', Weight.manual)
async def cmd_new_pressure(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.answer('Внесите новое значение веса в кг')
    sent_message = await call.message.answer('Введите текущий вес', reply_markup=None)
    user_messages[call.message.from_user.id] = [sent_message.message_id]
    await state.update_data(user_id=call.message.from_user.id)
    await state.set_state(Weight.weight)

@weight_router.message(F.text, Weight.manual)
async def cmd_new_pressure(message: Message, state: FSMContext):
    await state.update_data(user_id=message.from_user.id)
    weight = message.text
    if re.findall(r'\d{1,4},.+', weight):
        splits = weight.split(',')
        if len(splits) == 1:
            data = {'weight':float(splits[0]), 'comment': None}
        elif len(splits)==2:
            data = {'weight':float(splits[0]), 'comment': splits[1]}
        else:
            await message.answer(text=f'Ошибка в строке. Исправь и попробуй ещё раз')
            return
    else:
        await message.answer(text=f'Ошибка в строке. Исправь и попробуй ещё раз')
        return
    # await state.update_data(systolic=systolic)
    await state.update_data(**data)
    string = f"{data.get('weight')} кг"
    if data.get('comment'):
        string += f', {data.get('comment')}'
    sent_message = await message.answer(f'Проверьте, всё ли верно:\n{string}', reply_markup=check_data())
    user_messages[message.from_user.id] = [sent_message.message_id]
    await state.set_state(Weight.check_state)

@weight_router.message(F.text, Weight.weight)
async def cmd_new_pressure(message: Message, state: FSMContext):
    await state.update_data(user_id=message.from_user.id)
    weight = extract_cal(message.text)
    if not weight:
        sent_message = await message.answer('Введите вес корректно!', reply_markup=None)
        user_messages[message.from_user.id] = [sent_message.message_id]
        return
    await state.update_data(weight=weight)
    sent_message = await message.answer('Введите комм', reply_markup=create_skip_button())
    user_messages[message.from_user.id] = [sent_message.message_id]
    await state.set_state(Weight.comment)


@weight_router.message(F.text, Weight.comment)
async def cmd_new_pressure(message: Message, state: FSMContext):
    comment = message.text
    await state.update_data(comment=comment)
    data = await state.get_data()
    string = f"{data.get('weight')}"
    if data.get('comment'):
        string+=f', {data.get('comment')}'
    sent_message = await message.answer(f'Проверьте, всё ли верно:\n{string}', reply_markup=check_data())
    user_messages[message.from_user.id] = [sent_message.message_id]
    await state.set_state(Weight.check_state)

@weight_router.callback_query(F.data == 'skip_question', Weight.comment)
async def cmd_new_pressure(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    string = f"{data.get('weight')}"
    if data.get('comment'):
        string += f', {data.get('comment')}'
    sent_message = await call.message.answer(f'Проверьте, всё ли верно:\n{string}', reply_markup=check_data())
    user_messages[call.message.from_user.id] = [sent_message.message_id]
    await call.answer('Без комментариев...')
    await state.set_state(Weight.check_state)

@pressure_router.callback_query(F.data=='correct', Pressure.check_state)
async def cmd_new_pressure(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    data.pop('sent_message')
    await state.update_data(user_id=call.from_user.id)
    pressure_id = await add_pressure_measurement(**data)
    await call.message.edit_reply_markup(reply_markup=None)
    await call.message.delete()
    await delete_messages(call, state)
    await call.answer('Данные записаны', show_alert=True)

@pressure_router.callback_query(F.data=='incorrect', Pressure.check_state)
async def cmd_new_pressure(call: CallbackQuery, state: FSMContext):
    await call.answer('Новое измерение давления')
    await call.message.edit_reply_markup(reply_markup=None)
    await call.message.delete()
    await call.message.answer('Введите систолическое давление: ')
    await state.set_state(Pressure.systolic)


@pressure_router.callback_query(F.data=='import_pressure')
async def cmd_new_pressure(call: CallbackQuery, state: FSMContext):
    await call.answer('Ручной ввод показателей давления')
    await call.message.answer(f'Введите показатели артериального давления вручную, каждое на новой строке,'
                              f' в формате "дата время давление пульс комментарий" вот так:'
                              f'{datetime.now().strftime("%d.%m.%Y %H:%M")} 120/80 66 После нагрузки')
    await state.set_state(Pressure.import_pressure)

@pressure_router.message(F.text.regexp(r'\d{2}\..+'), Pressure.import_pressure)
async def cmd_new_pressure(message: Message, state: FSMContext):
    user_id = message.from_user.id
    pressures = [x.strip() for x in message.text.split('\n')]
    items = []
    for idx, pressure in enumerate(pressures):
        if re.findall(r'\d{2}\.\d{2}\.\d{4} \d{2}:\d{2} \d{2,4}/\d{2,4} \d{2,4}', pressure):
            splits = pressure.split(' ')
            if len(splits) == 4:
                items.append({'date':datetime.strptime(splits[0]+' '+splits[1], '%d.%m.%Y %H:%M'),
                              'systolic':splits[2].split('/')[0], 'diastolic':splits[2].split('/')[1],
                              'pulse':splits[3], 'comment':None})
            else:
                items.append({'date':datetime.strptime(splits[0]+' '+splits[1], '%d.%m.%Y %H:%M'),
                              'systolic':splits[2].split('/')[0], 'diastolic':splits[2].split('/')[1],
                              'pulse':splits[3], 'comment':' '.join(splits[4:])})
        else:
            await message.answer(text=f'Ошибка в строке {idx+1}. Исправь и попробуй ещё раз')
            return
    await message.answer(text=f'Проверьте, всё ли верно: {calculate_nutrition_per_100g(items)}')



    await message.answer(text=f'Все ли верно:\n{"\n".join(pressures)}')

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