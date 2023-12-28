import telebot
from utils import *
token = "6791557722:AAEAEsN-xRCfIicXpK1PSMgjo2MtEUNDuM8"
bot = telebot.TeleBot(token)

@bot.message_handler(commands=["enter_items"])
def enter_items(message: telebot.types.Message):
    bot.send_message(message.chat.id, "Введите через запятую ссылки на предметы Steam")
    bot.register_next_step_handler(message, input_links)
def input_links(message: telebot.types.Message):
    try:
        items = Item(message.text.split(","), message.chat.id)
        print(1)
        items.write_item()
    except Exception as ex:
        bot.send_message(message.chat.id, "Что-то пошло не так!")
        print(ex)

@bot.message_handler(commands=["start"])
def start(message: telebot.types.Message):
    bot.send_message(message.chat.id, "Это бот для вывода информации о предметах на торговой площадке Steam")

bot.polling(none_stop=True)