import telebot
import random
import shelve

from config import bot_token, db_name

bot = telebot.TeleBot(bot_token)

DIGITS = [str(x) for x in range(10)]

@bot.message_handler(commands=['start', 'game'])
def start_game(message):
    digits = DIGITS.copy()
    my_number = ''
    for pos in range(4):
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
        f'Я загадал 4-значное число. Попробуй отгадать, {message.from_user.first_name}!')

@bot.message_handler(commands=['help'])
def show_help(message):
    bot.reply_to(message, """
Игра Быки и коровы

Игра, в ходе которой за несколько попыток игрок должен определить 4-значное число, задуманное ботом. После каждой попытки бот сообщает количество угаданных цифр без с их позициями (количество «коров») и полных совпадений (количество «быков»).
""")

@bot.message_handler(content_types=['text'])
def bot_answer(message):
    global active_game
    text = message.text
    try:
        with shelve.open(db_name) as storage:
            my_number = storage[str(message.from_user.id)]
        if len(text) == 4 and text.isnumeric() and len(text) == len(set(text)):
            cows, bulls = 0, 0
            for i in range(4):
                if text[i] in my_number:
                    if text[i] == my_number[i]:
                        bulls += 1
                    else:
                        cows += 1
            if bulls == 4:
                print(f'{my_number} was discovered by {message.from_user.username} !')
                with shelve.open(db_name) as storage:
                    del storage[str(message.from_user.id)]
                response = 'Ты угадал! Сыграем еще?\n\n' + \
                           '_Приходи учиться в Кит создавать ботов для Telegram_\n' + \
                           'https://kit.kh.ua/'
                bot.send_message(message.from_user.id, response,
                    reply_markup=get_buttons(), parse_mode='Markdown')
                return
            else:
                response = f'Быки: {bulls} | Коровы : {cows}'
        else:
            response = 'Пришли мне 4-значное число с разными цифрами!'
    except KeyError:
        if text == 'Да':
            start_game(message)
            return
        else:
            response = 'Для запуска игры набери /start'
    bot.send_message(message.from_user.id, response)

def get_buttons():
    buttons = telebot.types.ReplyKeyboardMarkup(
        one_time_keyboard=True,
        resize_keyboard=True
    )
    buttons.add('Да', 'Нет')
    return buttons

if __name__ == '__main__':
    bot.polling(non_stop=True)
