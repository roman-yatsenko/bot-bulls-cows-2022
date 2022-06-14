import telebot
import random
from itertools import product

from config import bot_token
from user import del_user, get_or_create_user, save_user

bot = telebot.TeleBot(bot_token)

DIGITS = [str(x) for x in range(10)]

@bot.message_handler(commands=['start', 'game'])
def select_mode(message):
    del_user(message.from_user.id)
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
    user = get_or_create_user(message.from_user.id)
    user.number = my_number
    user.level = level
    save_user(message.from_user.id, user)
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
    user = get_or_create_user(message.from_user.id)
    # Если режим загадал человек, то бот отправляет свой вариант
    if not user.number and not user.level:
        bot_answer_not_in_game(message)
    elif user.mode == 'Бот':
        bot_answer_to_man_guess(message, user.number)
    else:
        bot_answer_with_guess(message)

def bot_answer_not_in_game(message):
    text = message.text
    user = get_or_create_user(message.from_user.id)
    if text in ('Человек', 'Бот'):
        user.mode = text
        save_user(message.from_user.id, user)
        select_level(message)
    elif text in ('3', '4', '5'):
        if user.mode != 'Бот':
            user.level = int(text)
            save_user(message.from_user.id, user)
            bot_answer_with_guess(message)
        else:
            start_game(message, int(text))
    elif text == 'Да':
        select_mode(message)
    else:
        response = f'Пришли мне /start или /game для запуска игры'
        bot.send_message(message.from_user.id, response)

def bot_answer_to_man_guess(message, my_number):
    level = len(my_number)
    text = message.text 
    if len(text) == level and text.isnumeric() and len(text) == len(set(text)):
        bulls, cows = bulls_n_cows(my_number, text)
        if bulls == level:
            print(f'{my_number} was discovered by {message.from_user.username} !')
            del_user(message.from_user.id)
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

def bot_answer_with_guess(message):
    user = get_or_create_user(message.from_user.id)
    if check_bot_win(user, message):
        return
    history = list(user.history)
    all_variants = [''.join(x) for x in product(DIGITS, repeat=user.level)
                    if len(x) == len(set(x)) and x[0] != '0']
    while all_variants:
        guess = random.choice(all_variants)
        all_variants.remove(guess)
        if is_compatible(guess, history):
            break
    else:
        del_user_with_message(
            message.from_user.id,
            text = 'К сожалению, в твоих ответах была ошибка,' \
                   'у меня больше нет вариантов :-('
        )
        return
    history.append((guess, None, None))
    user.history = tuple(history)
    save_user(message.from_user.id, user)
    keys = []
    for bulls in range(user.level + 1):
        for cows in range(user.level + 1 - bulls):
            keys.append(f'{bulls}-{cows}')
    response = f'Мой вариант {guess}\n' + \
                'Сколько быков и коров я угадал?'
    bot.send_message(message.from_user.id, response,
        reply_markup=get_buttons(*keys))

def check_bot_win(user, message):
    history = list(user.history)
    if history:
        history[-1] = (history[-1][0], *[int(x) for x in message.text.split('-')])
        # check win
        if history[-1][1] == user.level:
            del_user_with_message(
            message.from_user.id,
            text = 'Я угадал :-)\n' \
                   'Пришли мне /start или /game для запуска игры'
            )
            return True
        user.history = tuple(history)
        save_user(message.from_user.id, user)
    return False
    
def del_user_with_message(id, text):
    del_user(id)
    bot.send_message(id, text)

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

def is_compatible(guess, history):
    return all(bulls_n_cows(guess, previous_guess) == (bulls, cows) 
               for previous_guess, bulls, cows in history)

if __name__ == '__main__':
    print('Bot started')
    bot.polling(non_stop=True)
