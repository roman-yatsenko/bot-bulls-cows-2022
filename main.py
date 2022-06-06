import telebot
import random
from config import bot_token

bot = telebot.TeleBot(bot_token)

DIGITS = [str(x) for x in range(10)]
my_number = ''

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
    bot.reply_to(message, 
        f'Я загадал 4-значное число. Попробуй отгадать, {message.from_user.first_name}!')

if __name__ == '__main__':
    bot.polling(non_stop=True)
