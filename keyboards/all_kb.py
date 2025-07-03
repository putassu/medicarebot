from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from create_bot import admins
hours = ['00','01','02','03','04','05','06','07','08','09',
 '10', '11', '12', '13', '14', '15', '16', '17', '18',
 '19', '20', '21', '22', '23', '24']
minutes = ['00', '05', '10', '15', '20', '25', '30', '35', '40', '45', '50', '55']

def main_kb(user_telegram_id: int):
    kb_list = [
        [KeyboardButton(text="📖 О нас"), KeyboardButton(text="👤 Мой профиль"), KeyboardButton(text="📝 Заполнить анкету")],
        [KeyboardButton(text="🥬 Моё меню"), KeyboardButton(text="🍵 Дневник питания"), KeyboardButton(text="🩺 Моё давление")],
        [KeyboardButton(text="💊 Моя таблетница")]
    ]
    if user_telegram_id in admins:
        kb_list.append([KeyboardButton(text="⚙️ Админ панель")])
    keyboard = ReplyKeyboardMarkup(
        keyboard=kb_list,
        resize_keyboard=True,
        one_time_keyboard=False,
        input_field_placeholder="Воспользуйтесь меню:"
    )
    return keyboard

def gender_kb():
    kb_list = [
        [KeyboardButton(text="👨‍🦱Мужчина")], [KeyboardButton(text="👩‍🦱Женщина")]
    ]
    keyboard = ReplyKeyboardMarkup(keyboard=kb_list,
                                   resize_keyboard=True,
                                   one_time_keyboard=True,
                                   input_field_placeholder="Выбери пол:")
    return keyboard