import telebot
import random
import shelve

from config import bot_token, db_name

bot = telebot.TeleBot(bot_token)

DIGITS = [str(x) for x in range(10)]

@bot.message_handler(commands=['start', 'game'])
def select_mode(message):
    with shelve.open(db_name) as storage:
        if str(message.from_user.id) in storage:
            del storage[str(message.from_user.id)]
            del storage[str(message.from_user.id) + '__mode']
    response = 'Игра "Быки и коровы"\n' + \
               'Выбери кто загадывает число'
    bot.send_message(message.from_user.id, response,
        reply_markup=get_buttons('Человек', 'Бот'))    

def select_level(message):
    response = 'Игра "Быки и коровы"\n' + \
               'Выбери уровень (количество цифр)'
    bot.send_message(message.from_user.id, response,
        reply_markup=get_buttons('3', '4', '5'))    

def start_game(message, level):
    digits = DIGITS.copy()
    my_number = ''
    for pos in range(level):
        if pos:
            digit = random.choice(digits)
        else: 
            digit = random.choice(digits[1:])
        my_number += digit
        digits.remove(digit)
    print(f'{my_number} for {message.from_user.username}')
    with shelve.open(db_name) as storage:
        storage[str(message.from_user.id)] = my_number
    bot.reply_to(message, 'Игра "Быки и коровы"\n'
        f'Я загадал {level}-значное число. Попробуй отгадать, {message.from_user.first_name}!')

@bot.message_handler(commands=['help'])
def show_help(message):
    bot.reply_to(message, """
Игра Быки и коровы

Игра, в ходе которой за несколько попыток игрок должен определить 4-значное число, задуманное ботом. После каждой попытки бот сообщает количество угаданных цифр без с их позициями (количество «коров») и полных совпадений (количество «быков»).
""")

@bot.message_handler(content_types=['text'])
def bot_answer(message):
    text = message.text
    with shelve.open(db_name) as storage:
        if str(message.from_user.id) in storage:
            my_number = storage[str(message.from_user.id)]
        else:
            my_number = ''
    if not my_number:
        bot_answer_not_in_game(message)
    else:
        bot_answer_to_man_guess(message, my_number)

def bot_answer_not_in_game(message):
    text = message.text
    if text in ('Человек', 'Бот'):
        with shelve.open(db_name) as storage:
            storage[str(message.from_user.id) + '__mode'] = text
        select_level(message)
    if text in ('3', '4', '5'):
        start_game(message, int(text))
    elif text == 'Да':
        select_mode(message)
    return

def bot_answer_to_man_guess(message, my_number):
    level = len(my_number)
    text = message.text 
    if len(text) == level and text.isnumeric() and len(text) == len(set(text)):
        bulls, cows = bulls_n_cows(my_number, text)
        if bulls == level:
            print(f'{my_number} was discovered by {message.from_user.username} !')
            with shelve.open(db_name) as storage:
                del storage[str(message.from_user.id)]
            response = 'Ты угадал! Сыграем еще?\n\n' + \
                    '_Приходи учиться в Кит создавать ботов для Telegram_\n' + \
                    'https://kit.kh.ua/'
            bot.send_message(message.from_user.id, response,
                reply_markup=get_buttons('Да', 'Нет'), parse_mode='Markdown')
            return
        else:
            response = f'Быки: {bulls} | Коровы : {cows}'
    else:
        response = f'Пришли мне {level}-значное число с разными цифрами!'
    bot.send_message(message.from_user.id, response)

def get_buttons(*args):
    buttons = telebot.types.ReplyKeyboardMarkup(
        one_time_keyboard=True,
        resize_keyboard=True
    )
    buttons.add(*args)
    return buttons

def bulls_n_cows(a, b):
    bulls = sum(1 for x, y in zip(a, b) if x == y)
    cows = len(set(a) & set(b)) - bulls
    return bulls, cows

if __name__ == '__main__':
    bot.polling(non_stop=True)
