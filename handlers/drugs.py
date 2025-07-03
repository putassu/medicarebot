from aiogram import Router, F
from aiogram.filters import CommandStart, Command, CommandObject
from aiogram.types import Message
from keyboards.all_kb import main_kb, gender_kb
from keyboards.inline_kbs import (create_qst_inline_kb, get_login_tg,
                                  check_data, get_questionnaire, create_skip_button,
                                  create_yes_no_kb, get_new_meal_kb, get_products_inline_kb,
                                  get_new_product_kb, create_add_product_button, get_pressure_kb,
                                  get_drugs_units_kb, get_drugs_inline_kb)


from utils.utils import get_random_person, get_msc_date, extract_number
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
                                      add_pressure_measurement, get_pressures, insert_drug, insert_drug_adm,
                                      get_drugs_by_user)
from datetime import datetime
import re
#
bot_id = 7307476763
class Drug(StatesGroup):
    manual = State()
    name = State()
    measure = State()
    dosage = State()
    admtime = State()
    check_state = State()
    import_drugs = State()

drug_router = Router()
user_messages = {}
drug_router.message.filter(lambda message: message.photo or (message.text and not message.text.startswith('/')))
#
@drug_router.callback_query(F.data == 'new_drug')
async def cmd_new_pressure(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.answer('Введите название лекарства')
    sent_message = await call.message.answer('Введите название лекарства', reply_markup=None)
    user_messages[call.message.from_user.id] = [sent_message.message_id]
    await state.update_data(user_id=call.message.from_user.id)
    await state.set_state(Drug.name)
#
# @pressure_router.message(F.text, Pressure.manual)
# async def cmd_new_pressure(message: Message, state: FSMContext):
#     await state.update_data(user_id=message.from_user.id)
#     pressure = message.text
#     if re.findall(r'\d{2,4}/\d{2,4},\s*\d{2,4}', pressure):
#         splits = pressure.split(',')
#         if len(splits) == 2:
#             data = {'systolic': int(splits[0].split('/')[0]), 'diastolic': int(splits[0].split('/')[1]),
#                           'pulse': int(splits[1]), 'comment': None}
#         elif len(splits) > 2:
#             data = {'systolic': int(splits[0].split('/')[0]), 'diastolic': int(splits[0].split('/')[1]),
#                           'pulse': int(splits[1]), 'comment': ' '.join(splits[2:])}
#         else:
#             await message.answer(text=f'Ошибка в строке. Исправь и попробуй ещё раз')
#             return
#     else:
#         await message.answer(text=f'Ошибка в строке. Исправь и попробуй ещё раз')
#         return
#     # await state.update_data(systolic=systolic)
#     await state.update_data(**data)
#     string = f"{data.get('systolic')}/{data.get('diastolic')}, {data.get('pulse')}"
#     if data.get('comment'):
#         string += f', {data.get('comment')}'
#     sent_message = await message.answer(f'Проверьте, всё ли верно:\n{string}', reply_markup=check_data())
#     user_messages[message.from_user.id] = [sent_message.message_id]
#     await state.set_state(Pressure.check_state)
#
@drug_router.message(F.text, Drug.name)
async def cmd_new_pressure(message: Message, state: FSMContext):
    await state.update_data(user_id=message.from_user.id)
    name = message.text
    await state.update_data(name = name)
    sent_message = await message.answer('Выберите единицы измерения дозировки лекарства', reply_markup=get_drugs_units_kb())
    user_messages[message.from_user.id] = [sent_message.message_id]
    await state.set_state(Drug.measure)

@drug_router.callback_query(F.data.in_(['g','mg','mkg']), Drug.measure)
async def cmd_new_pressure(call: CallbackQuery, state: FSMContext):
    await state.update_data(measure=call.data)
    await call.answer()
    sent_message = await call.message.answer(f'Введите дозировку в {call.data}')
    user_messages[call.message.from_user.id] = [sent_message.message_id]
    await state.set_state(Drug.dosage)

@drug_router.message(F.text, Drug.dosage)
async def cmd_new_pressure(message: Message, state: FSMContext):
    await state.update_data(user_id=message.from_user.id)
    dosage = extract_cal(message.text)
    await state.update_data(dosage = dosage)
    sent_message = await message.answer('Во сколько вам нужно принять лекарство? Пример ввода: <b>09:30</b>')
    user_messages[message.from_user.id] = [sent_message.message_id]
    await state.set_state(Drug.admtime)

@drug_router.message(F.text, Drug.admtime)
async def cmd_new_pressure(message: Message, state: FSMContext):
    await state.update_data(user_id=message.from_user.id)
    admtime = message.text
    await state.update_data(admtime=admtime)
    data = await state.get_data()
    sent_message = await message.answer(f'Проверьте, всё ли верно: {data}', reply_markup=check_data())
    user_messages[message.from_user.id] = [sent_message.message_id]
    await state.set_state(Drug.check_state)
#
# @pressure_router.message(F.text, Pressure.diastolic)
# async def cmd_new_pressure(message: Message, state: FSMContext):
#     diastolic = extract_number(message.text)
#     if not diastolic:
#         sent_message = await message.answer('Введите диастолическое давление корректно!', reply_markup=None)
#         user_messages[message.from_user.id] = [sent_message.message_id]
#         return
#     await state.update_data(diastolic=diastolic)
#     sent_message = await message.answer('Введите пульс', reply_markup=None)
#     user_messages[message.from_user.id] = [sent_message.message_id]
#     await state.set_state(Pressure.pulse)
#
# @pressure_router.message(F.text, Pressure.pulse)
# async def cmd_new_pressure(message: Message, state: FSMContext):
#     pulse = extract_number(message.text)
#     if not pulse:
#         sent_message = await message.answer('Введите пульс корректно!', reply_markup=None)
#         user_messages[message.from_user.id] = [sent_message.message_id]
#         return
#     await state.update_data(pulse=pulse)
#     sent_message = await message.answer('Добавьте комментарий', reply_markup=create_skip_button())
#     user_messages[message.from_user.id] = [sent_message.message_id]
#     await state.set_state(Pressure.comment)
#
# @pressure_router.message(F.text, Pressure.comment)
# async def cmd_new_pressure(message: Message, state: FSMContext):
#     comment = message.text
#     await state.update_data(comment=comment)
#     data = await state.get_data()
#     string = f"{data.get('systolic')}/{data.get('diastolic')}, {data.get('pulse')}"
#     if data.get('comment'):
#         string+=f', {data.get('comment')}'
#     sent_message = await message.answer(f'Проверьте, всё ли верно:\n{string}', reply_markup=check_data())
#     user_messages[message.from_user.id] = [sent_message.message_id]
#     await state.set_state(Pressure.check_state)
#
# @pressure_router.callback_query(F.data == 'skip_question', Pressure.comment)
# async def cmd_new_pressure(call: CallbackQuery, state: FSMContext):
#     data = await state.get_data()
#     string = f"{data.get('systolic')}/{data.get('diastolic')}, {data.get('pulse')}"
#     if data.get('comment'):
#         string += f', {data.get('comment')}'
#     sent_message = await call.message.answer(f'Проверьте, всё ли верно:\n{string}', reply_markup=check_data())
#     user_messages[call.message.from_user.id] = [sent_message.message_id]
#     await call.answer('Без комментариев...')
#     await state.set_state(Pressure.check_state)
#
@drug_router.callback_query(F.data=='correct', Drug.check_state)
async def cmd_new_pressure(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await state.update_data(user_id=call.from_user.id)
    data = await state.get_data()
    await insert_drug(**data)
    # pressure_id = await add_pressure_measurement(**data)
    await call.message.edit_reply_markup(reply_markup=None)
    await call.message.delete()
    await delete_messages(call, state)
    await call.answer('Данные записаны', show_alert=True)

@drug_router.callback_query(F.data=='incorrect', Drug.check_state)
async def cmd_new_pressure(call: CallbackQuery, state: FSMContext):
    await call.answer('Начать заново')
    await call.message.edit_reply_markup(reply_markup=None)
    await call.message.delete()
    await call.message.answer('Введите название лекарства:')
    await state.set_state(Drug.name)

@drug_router.callback_query((F.data.startswith('view_drug:')))
async def cmd_new_pressure(call: CallbackQuery, state: FSMContext):
    drug = call.data
    _, user_id, drug_id = drug.split(':')
    await insert_drug_adm(int(drug_id))
    await call.answer('Отметка о приёме поставлена')
    items = await get_drugs_by_user(int(user_id))
    await call.message.edit_reply_markup(reply_markup=get_drugs_inline_kb(0, user_id, items))

#
#
# @pressure_router.callback_query(F.data=='import_pressure')
# async def cmd_new_pressure(call: CallbackQuery, state: FSMContext):
#     await call.answer('Ручной ввод показателей давления')
#     await call.message.answer(f'Введите показатели артериального давления вручную, каждое на новой строке,'
#                               f' в формате "дата время давление пульс комментарий" вот так:'
#                               f'{datetime.now().strftime("%d.%m.%Y %H:%M")} 120/80 66 После нагрузки')
#     await state.set_state(Pressure.import_pressure)
#
# @pressure_router.message(F.text.regexp(r'\d{2}\..+'), Pressure.import_pressure)
# async def cmd_new_pressure(message: Message, state: FSMContext):
#     user_id = message.from_user.id
#     pressures = [x.strip() for x in message.text.split('\n')]
#     items = []
#     for idx, pressure in enumerate(pressures):
#         if re.findall(r'\d{2}\.\d{2}\.\d{4} \d{2}:\d{2} \d{2,4}/\d{2,4} \d{2,4}', pressure):
#             splits = pressure.split(' ')
#             if len(splits) == 4:
#                 items.append({'date':datetime.strptime(splits[0]+' '+splits[1], '%d.%m.%Y %H:%M'),
#                               'systolic':splits[2].split('/')[0], 'diastolic':splits[2].split('/')[1],
#                               'pulse':splits[3], 'comment':None})
#             else:
#                 items.append({'date':datetime.strptime(splits[0]+' '+splits[1], '%d.%m.%Y %H:%M'),
#                               'systolic':splits[2].split('/')[0], 'diastolic':splits[2].split('/')[1],
#                               'pulse':splits[3], 'comment':' '.join(splits[4:])})
#         else:
#             await message.answer(text=f'Ошибка в строке {idx+1}. Исправь и попробуй ещё раз')
#             return
#     await message.answer(text=f'Проверьте, всё ли верно: {items}')
#
#
#
#     await message.answer(text=f'Все ли верно:\n{"\n".join(pressures)}')
#
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