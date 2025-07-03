from aiogram import Router, F
from aiogram.filters import CommandStart, Command, CommandObject
from aiogram.types import Message
from keyboards.all_kb import main_kb, gender_kb
from keyboards.inline_kbs import (create_qst_inline_kb, get_login_tg, check_data,
                                  get_questionnaire, create_skip_button, get_activity_levels_kb)
from utils.utils import (get_random_person, get_msc_date, extract_number,
                         extract_year, get_timezone, extract_height)
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from create_bot import questions
import asyncio
from aiogram.utils.chat_action import ChatActionSender
from create_bot import bot, admins
from aiogram.types import ReplyKeyboardRemove
from aiogram.fsm.state import State, StatesGroup
from db_handler.postgres_func import get_profile, upsert_profile, get_activity_levels_list
from html import escape


class Form(StatesGroup):
    gender = State()
    age = State()
    full_name = State()
    user_login = State()
    city = State()
    timezone = State()
    activity_level = State()
    height = State()
    weight = State()
    check_state = State()


questionnaire_router = Router()
questionnaire_router.message.filter(lambda message: message.photo or (message.text and not message.text.startswith('/')))

@questionnaire_router.message((F.text == '📝 Заполнить анкету'))
async def start_questionnaire_process(message: Message, state: FSMContext):
    await state.clear()
    async with ChatActionSender.typing(bot=bot, chat_id=message.chat.id):
        await message.answer('Привет. Для начала выбери свой пол: ', reply_markup=gender_kb())
    await state.set_state(Form.gender)

@questionnaire_router.callback_query(F.data == 'fill_profile')
async def start_questionnaire_process(call: CallbackQuery, state: FSMContext):
    await state.clear()
    async with ChatActionSender.typing(bot=bot, chat_id=call.message.chat.id):
        await call.message.answer('Привет. Для начала выбери свой пол - это важно для определения уровня обмена: ', reply_markup=gender_kb())
        await call.answer()
    await state.set_state(Form.gender)


@questionnaire_router.message((F.text.lower().contains('мужчина')) | (F.text.lower().contains('женщина')), Form.gender)
async def start_questionnaire_process(message: Message, state: FSMContext):
    await state.update_data(gender=message.text, user_id=message.from_user.id)
    async with ChatActionSender.typing(bot=bot, chat_id=message.chat.id):
        await message.answer('Супер! А теперь напиши год своего рождения - твой'
                             ' возраст нужен для расчета физиологических показателей и норм: ', reply_markup=ReplyKeyboardRemove())
    await state.set_state(Form.age)


@questionnaire_router.message(F.text, Form.gender)
async def start_questionnaire_process(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    async with ChatActionSender.typing(bot=bot, chat_id=message.chat.id):
        await message.answer('Пожалуйста, выбери вариант из тех что в клавиатуре: ', reply_markup=gender_kb())
    await state.set_state(Form.gender)


@questionnaire_router.message(F.text, Form.age)
async def start_questionnaire_process(message: Message, state: FSMContext):
    check_age = extract_year(message.text)

    if not check_age:
        await message.reply("Пожалуйста, введите корректный год (число от 1900 до 2024).")
        return

    await state.update_data(age=check_age)
    await message.answer('Теперь укажите свое полное имя:', reply_markup=create_skip_button())
    await state.set_state(Form.full_name)

@questionnaire_router.callback_query(F.data == 'skip_question', Form.full_name)
async def start_questionnaire_process(message: Message, state: FSMContext):
    await state.update_data(full_name=None)
    text = 'Теперь укажите ваш логин, который будет использоваться в боте'

    if message.from_user.username:
        text += ' или нажмите на кнопку ниже и в этом случае вашим логином будет логин из вашего телеграмм: '
        await message.answer(text, reply_markup=get_login_tg())
    else:
        text += ' : '
        await message.answer(text)

    await state.set_state(Form.user_login)


@questionnaire_router.message(F.text, Form.full_name)
async def start_questionnaire_process(message: Message, state: FSMContext):
    await state.update_data(full_name=message.text)
    text = 'Теперь укажите ваш логин, который будет использоваться в боте'

    if message.from_user.username:
        text += ' или нажмите на кнопку ниже и в этом случае вашим логином будет логин из вашего телеграмм: '
        await message.answer(text, reply_markup=get_login_tg())
    else:
        text += ' : '
        await message.answer(text)

    await state.set_state(Form.user_login)

# вариант когда мы берем логин из профиля телеграмм
@questionnaire_router.callback_query(F.data, Form.user_login)
async def start_questionnaire_process(call: CallbackQuery, state: FSMContext):
    await call.answer('Беру логин с телеграмм профиля')
    await call.message.edit_reply_markup(reply_markup=None)
    await state.update_data(user_login=call.from_user.username)
    await call.message.answer('А теперь напиши город из твоего часового пояса: ')
    await state.set_state(Form.city)


# вариант когда мы берем логин из введенного пользователем
@questionnaire_router.message(F.text, Form.user_login)
async def start_questionnaire_process(message: Message, state: FSMContext):
    await state.update_data(user_login=message.text)
    await message.answer('А теперь напиши город - это нужно для расчёта часового пояса: ')
    await state.set_state(Form.city)

@questionnaire_router.message(F.text, Form.city)
async def start_questionnaire_process(message: Message, state: FSMContext):
    tz, address = get_timezone(message.text)
    if not tz:
        await message.reply("Упс, произошла ошибка при определении часового пояса. "
                            "Пожалуйста, попробуйте набрать название на английском или введите другой город")
        return

    await state.update_data(city = address, timezone = tz)
    activity_levels = await get_activity_levels_list()
    activity_levels_card = '\n'.join([f'<b>{level.activity_level}. {level.description}</b>' for level in activity_levels])

    await message.answer(f'Теперь выберите один из следующих уровней активности:\n{activity_levels_card}',
                         reply_markup=get_activity_levels_kb())
    await state.set_state(Form.activity_level)

@questionnaire_router.callback_query(F.data, Form.activity_level)
async def start_questionnaire_process(call: CallbackQuery, state: FSMContext):
    level = call.data
    await call.answer(f'Выбран уровень {level}')
    await call.message.edit_reply_markup(reply_markup=None)
    await state.update_data(activity_level=int(level))
    await call.message.answer('А теперь введи свой рост в см: ')
    await state.set_state(Form.height)

@questionnaire_router.message(F.text, Form.height)
async def start_questionnaire_process(message: Message, state: FSMContext):
    check_height = extract_height(message.text)

    if not check_height:
        await message.reply("Пожалуйста, введите рост в см (число от 10 до 300).")
        return

    await state.update_data(height=check_height)
    await message.answer('Теперь укажите свой вес в кг:', reply_markup=create_skip_button())
    await state.set_state(Form.weight)

@questionnaire_router.message(F.text, Form.weight)
async def start_questionnaire_process(message: Message, state: FSMContext):
    check_weight = extract_height(message.text)

    if not check_weight:
        await message.reply("Пожалуйста, введите вес в кг (число от 10 до 300).")
        return

    await state.update_data(weight=check_weight)
    data = await state.get_data()
    caption = f'Пожалуйста, проверьте, всё ли верно: \n\n' \
                  f'<b>Полное имя</b>: {escape(data.get('full_name')) if data.get('full_name') else ' - '}\n' \
                  f'<b>Пол</b>: {data.get('gender') if data.get('gender') else ' - '}\n' \
                  f'<b>Возраст</b>: {data.get('age') if data.get('age') else ' - '} лет\n' \
                  f'<b>Логин в боте</b>: {escape(data.get('user_login')) if data.get('user_login') else ' - '}\n' \
                  f'<b>Город</b>: {escape(data.get('city')) if data.get('city') else ' - '}\n' \
              f'<b>Часовой пояс</b>: {escape(data.get('timezone')) if data.get('timezone') else ' - '}\n' \
              f'<b>Уровень активности</b>: {data.get('activity_level') if data.get('activity_level') else ' - '}\n' \
                      f'<b>Мой текущий рост</b>: {data.get('height') if data.get('height') else ' - '}\n' \
                f'<b>Мой текущий вес</b>: {data.get('weight') if data.get('weight') else ' - '}\n'

    await message.answer(text=caption, reply_markup=check_data())
    await state.set_state(Form.check_state)

@questionnaire_router.callback_query(F.data =='skip_question', Form.weight)
async def start_questionnaire_process(message: Message, state: FSMContext):
    await state.update_data(weight=None)
    data = await state.get_data()
    caption = f'Пожалуйста, проверьте, всё ли верно: \n\n' \
                  f'<b>Полное имя</b>: {escape(data.get('full_name')) if data.get('full_name') else ' - '}\n' \
                  f'<b>Пол</b>: {data.get('gender') if data.get('gender') else ' - '}\n' \
                  f'<b>Возраст</b>: {data.get('age') if data.get('age') else ' - '} лет\n' \
                  f'<b>Логин в боте</b>: {escape(data.get('user_login')) if data.get('user_login') else ' - '}\n' \
                  f'<b>Город</b>: {escape(data.get('city')) if data.get('city') else ' - '}\n' \
              f'<b>Часовой пояс</b>: {escape(data.get('timezone')) if data.get('timezone') else ' - '}\n' \
              f'<b>Уровень активности</b>: {data.get('activity_level') if data.get('activity_level') else ' - '}\n' \
                      f'<b>Мой текущий рост</b>: {data.get('height') if data.get('height') else ' - '}\n' \
                f'<b>Мой текущий вес</b>: {data.get('weight') if data.get('weight') else ' - '}\n'

    await message.answer(text=caption, reply_markup=check_data())
    await state.set_state(Form.check_state)
# @questionnaire_router.message(F.photo, Form.photo)
# async def start_questionnaire_process(message: Message, state: FSMContext):
#     photo_id = message.photo[-1].file_id
#     await state.update_data(photo=photo_id)
#     await message.answer('А теперь расскажите пару слов о себе: ')
#     await state.set_state(Form.about)
#
#
# @questionnaire_router.message(F.document.mime_type.startswith('image/'), Form.photo)
# async def start_questionnaire_process(message: Message, state: FSMContext):
#     photo_id = message.document.file_id
#     await state.update_data(photo=photo_id)
#     await message.answer('А теперь расскажите пару слов о себе: ')
#     await state.set_state(Form.about)


# @questionnaire_router.message(F.document, Form.photo)
# async def start_questionnaire_process(message: Message, state: FSMContext):
#     await message.answer('Пожалуйста, отправьте фото!')
#     await state.set_state(Form.photo)



# сохраняем данные
@questionnaire_router.callback_query(F.data == 'correct', Form.check_state)
async def start_questionnaire_process(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    print(data)
    await upsert_profile(**data)
    await call.answer('Данные сохранены')
    await call.message.edit_reply_markup(reply_markup=None)
    await call.message.answer('Благодарю за регистрацию. Ваши данные успешно сохранены!')
    await state.clear()


# запускаем анкету сначала
@questionnaire_router.callback_query(F.data == 'incorrect', Form.check_state)
async def start_questionnaire_process(call: CallbackQuery, state: FSMContext):
    await call.answer('Запускаем сценарий с начала')
    await call.message.edit_reply_markup(reply_markup=None)
    await call.message.delete()
    await call.message.answer('Привет. Для начала выбери свой пол: ', reply_markup=gender_kb())
    await state.set_state(Form.gender)