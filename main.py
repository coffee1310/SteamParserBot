import telebot.types
from utils import *

token = "6791557722:AAEAEsN-xRCfIicXpK1PSMgjo2MtEUNDuM8"
bot = telebot.TeleBot(token)

last_time_message = {}

@bot.message_handler(commands=["show_item_info"])
def show_item_info(message: telebot.types.Message):
    items = get_items(message.chat.id)
    markup = telebot.types.InlineKeyboardMarkup()

    for item in items:
        btn = telebot.types.InlineKeyboardButton(item, callback_data=f"item {item}")
        markup.row(btn)
    bot.send_message(message.chat.id, "Выберите предмет", reply_markup=markup)
@bot.callback_query_handler(func=lambda callback: True)
def callback(callback):
    if callback.data.find("item") != -1:
        info = get_item_info(callback.message.chat.id, callback.data[5:])
        bot.send_message(callback.message.chat.id, f"*{info[0][1]}*\n"
                                                   f"   Название: {callback.data[5:]}\n"
                                                   f"   Цена: {info[0][0]}\n ", parse_mode="Markdown")

@bot.message_handler(commands=["enter_links"])
def enter_items(message: telebot.types.Message):
    if message.chat.id in last_time_message:
        current_time = time.time()
        interval = 20
        if current_time - last_time_message[message.chat.id] < interval:
            bot.send_message(message.chat.id, f"Подождите еще {current_time-last_time_message[message.chat.id]} секунд")
            return
    bot.send_message(message.chat.id, "Введите через запятую ссылки на предметы Steam")
    bot.register_next_step_handler(message, input_links)

def input_links(message: telebot.types.Message):
    last_time_message[message.chat.id] = time.time()

    try:
        chat_id = message.chat.id

        if message.text.find(",") != -1:
            items_list = message.text.split(",")
        else:
            items_list = [message.text]
        if " " in items_list:
            items_list = message.remove(" ")
        items = Item(items_list, chat_id)
        items.write_item()
    except Exception as ex:
        bot.send_message(message.chat.id, "Что-то пошло не так!")
        print(ex)

@bot.message_handler(commands=["start"])
def start(message: telebot.types.Message):
    bot.send_message(message.chat.id, "Это бот для вывода информации о предметах на торговой площадке Steam")
    markup = telebot.types.ReplyKeyboardMarkup()
    btn1 = telebot.types.KeyboardButton("Добавить ссылки")
    bot.send_message(message.chat.id, "Команды", reply_markup=markup)
    markup.row(btn1)

bot.polling(none_stop=True)