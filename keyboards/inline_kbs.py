from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder
from db_handler.postgres_func import get_activity_levels_list
from datetime import datetime

def change_profile_kb():
    inline_kb_list = [
        [InlineKeyboardButton(text="Изменить", callback_data='change_profile')],
        [InlineKeyboardButton(text="На главную", callback_data='back_home')]
    ]
    return InlineKeyboardMarkup(inline_keyboard=inline_kb_list)


def get_new_product_kb():
    button = InlineKeyboardButton(text="Новый продукт", callback_data='new_product')
    # Создаем клавиатуру с добавлением кнопки в список
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[button]])
    return keyboard
    return keyboard

def get_new_meal_kb(product_id, weight):
    if weight!='None':
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Добавить в новый приём (в граммах)", callback_data=f'new_meal:grams:{product_id}:{weight}')],
             [InlineKeyboardButton(text="Добавить в новый приём (в штуках)", callback_data=f'new_meal:items:{product_id}:{weight}')],
            [InlineKeyboardButton(text="Удалить продукт", callback_data=f'product:delete:{product_id}')]])
    else:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Добавить в новый приём (в граммах)",
                                  callback_data=f'new_meal:grams:{product_id}:')],
            [InlineKeyboardButton(text="Удалить продукт", callback_data=f'product:delete:{product_id}')]])
    return keyboard

def get_products_inline_kb(page, user_id, items, max_items=6):
    builder = InlineKeyboardBuilder()
    subitems = items[page*max_items:(page+1)*max_items]
    for item in subitems:
        builder.row(
            InlineKeyboardButton(
                text=item.name,
                callback_data=f'view_product:{user_id}:{item.product_id}:{item.weight}'
            )
        )
    if page>0:
        builder.row(
            InlineKeyboardButton(
                text='◀️ Назад',
                callback_data=f'product_pagination:back:{user_id}:{page-1}'
            )
        )

    if page+1 < len(items)/max_items:
        builder.row(
            InlineKeyboardButton(
                text='Вперёд ▶️',
                callback_data=f'product_pagination:next:{user_id}:{page+1}'
            )
        )
    # Настраиваем размер клавиатуры
    builder.row(InlineKeyboardButton(text="Новый продукт ➕", callback_data='new_product'))
    builder.row(InlineKeyboardButton(text="Калькулятор калорийности по ингредиентам 🧮", callback_data='new_product_calc'))
    builder.adjust(2)
    return builder.as_markup()

def get_meals_inline_kb(page, user_id, items, max_items=6):
    builder = InlineKeyboardBuilder()
    subitems = items[page*max_items:(page+1)*max_items]
    for item in subitems:
        builder.row(
            InlineKeyboardButton(
                text=item['date'].strftime("%m/%d/%Y %H:%M:%S"),
                callback_data=f'view_meal:{user_id}:{item['meal_id']}'
            )
        )
    if page>0:
        builder.row(
            InlineKeyboardButton(
                text='◀️ Назад',
                callback_data=f'meal_pagination:back:{user_id}:{page-1}'
            )
        )

    if page+1 < len(items)/max_items:
        builder.row(
            InlineKeyboardButton(
                text='Вперёд ▶️',
                callback_data=f'meal_pagination:next:{user_id}:{page+1}'
            )
        )
    # Настраиваем размер клавиатуры
    builder.row(InlineKeyboardButton(text="Отчёт за неделю", callback_data='meals:week'))
    builder.row(InlineKeyboardButton(text="Отчёт за месяц", callback_data='meals:month'))
    builder.adjust(2)
    return builder.as_markup()


def create_qst_inline_kb(questions: dict) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    # Добавляем кнопки вопросов
    for question_id, question_data in questions.items():
        builder.row(
            InlineKeyboardButton(
                text=question_data.get('qst'),
                callback_data=f'qst_{question_id}'
            )
        )
    # Добавляем кнопку "На главную"
    builder.row(
        InlineKeyboardButton(
            text='На главную',
            callback_data='back_home'
        )
    )
    # Настраиваем размер клавиатуры
    builder.adjust(2)
    return builder.as_markup()

def get_login_tg():
    kb_list = [
        [InlineKeyboardButton(text="Использовать мой логин с ТГ", callback_data='in_login')]
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=kb_list)
    return keyboard

def check_data():
    kb_list = [
        [InlineKeyboardButton(text="✅Все верно", callback_data='correct')],
        [InlineKeyboardButton(text="❌Заполнить сначала", callback_data='incorrect')]
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=kb_list)
    return keyboard

def get_questionnaire():
    kb_list = [
        [InlineKeyboardButton(text="📝 Заполнить анкету", callback_data='fill_profile')]
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=kb_list)
    return keyboard

def create_skip_button() -> InlineKeyboardMarkup:
    kb_list = [
        [InlineKeyboardButton(text="Пропустить", callback_data='skip_question')]
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=kb_list)
    return keyboard

def create_yes_no_kb() -> InlineKeyboardMarkup:
    # Создаем инлайн-клавиатуру с кнопкой "Пропустить"
    kb_list = [
        [InlineKeyboardButton(text="✅Да", callback_data='yes')],
        [InlineKeyboardButton(text="❌Нет", callback_data='no')]
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=kb_list)
    return keyboard

def get_activity_levels_kb():
    kb_list = [[InlineKeyboardButton(text="1", callback_data='1'),
               InlineKeyboardButton(text="2", callback_data='2'),
               InlineKeyboardButton(text="3", callback_data='3'),
               InlineKeyboardButton(text="4", callback_data='4'),
               InlineKeyboardButton(text="5", callback_data='5')]]
    keyboard = InlineKeyboardMarkup(inline_keyboard=kb_list)
    return keyboard

def create_add_product_button():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Добавить ещё продукт", callback_data='add_another_product')],
        [InlineKeyboardButton(text="Завершить приём пищи", callback_data='finish_meal')],
        [InlineKeyboardButton(text="Пропустить", callback_data='skip_question')]
    ])

def get_pressure_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Внести измерение давления", callback_data='new_pressure')],
        [InlineKeyboardButton(text="Импорт измерений давления за период", callback_data='import_pressure')],
        [InlineKeyboardButton(text="Экспорт измерений давлений за период", callback_data='export_pressure')]
    ])

def get_drugs_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Добавить препарат", callback_data='new_drug')],
        [InlineKeyboardButton(text="Импорт приёмов лекарств за период", callback_data='import_drugs')],
        [InlineKeyboardButton(text="Экспорт приемов лекарств", callback_data='export_drugs')]
    ])

def get_drugs_units_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="мг", callback_data='mg'),InlineKeyboardButton(text="мкг", callback_data='mkg'),InlineKeyboardButton(text="г", callback_data='g')],
        [InlineKeyboardButton(text="мг", callback_data='mg'),InlineKeyboardButton(text="мкг", callback_data='mkg'),InlineKeyboardButton(text="г", callback_data='g')],
    ])

def get_drugs_inline_kb(page, user_id, items, max_items=6):
    builder = InlineKeyboardBuilder()
    subitems = items[page*max_items:(page+1)*max_items]
    for item in subitems:
        builder.row(
            InlineKeyboardButton(
                text=f'{item.name} {item.dosage} {item.measure} {item.admtime.strftime("%H:%M")}',
                callback_data=f'view_drug:{user_id}:{item.id}'
            )
        )
    if page>0:
        builder.row(
            InlineKeyboardButton(
                text='◀️ Назад',
                callback_data=f'drug_pagination:back:{user_id}:{page-1}'
            )
        )

    if page+1 < len(items)/max_items:
        builder.row(
            InlineKeyboardButton(
                text='Вперёд ▶️',
                callback_data=f'drug_pagination:next:{user_id}:{page+1}'
            )
        )
    # Настраиваем размер клавиатуры
    builder.row(InlineKeyboardButton(text="Новое лекарство ➕", callback_data='new_drug'))
    builder.row(InlineKeyboardButton(text="Импорт приёмов лекарств за период", callback_data='import_drugs'))
    builder.row(InlineKeyboardButton(text="Экспорт приемов лекарств", callback_data='export_drugs'))
    builder.row(InlineKeyboardButton(text="Удалить лекарство", callback_data='delete_drug'))
    builder.adjust(2)
    return builder.as_markup()