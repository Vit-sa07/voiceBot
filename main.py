import telebot
import requests
import os

bot_token = 'TOKEN'
bot = telebot.TeleBot(bot_token)
yandex_api_key = 'API'

voices = [
    {'name': 'jane', 'title': 'Джейн'},
    {'name': 'oksana', 'title': 'Оксана'},
    {'name': 'alyss', 'title': 'Алиса'},
    {'name': 'omazh', 'title': 'Омаш'},
    {'name': 'zahar', 'title': 'Захар'},
    {'name': 'ermil', 'title': 'Ермил'}
]


@bot.message_handler(commands=['start'])
def start(message):

    keybord = telebot.types.ReplyKeyboardMarkup(row_width=2)  # создает кнопки внизу чата
    btn1 = telebot.types.KeyboardButton('Конвертировать в текст📄')
    btn2 = telebot.types.KeyboardButton('Конвертировать в голос🎧')
    keybord.add(btn1, btn2)

    bot.reply_to(message, 'Привет! Я могу озвучить твое сообщение голосом. '
                 'Выбери голос, который хочешь использовать:', reply_markup=keybord)


@bot.message_handler(content_types=['text'])
def button(message):
    if message.text == 'Конвертировать в текст📄':
        a = bot.reply_to(message, 'Отправьте голосовое сообщение!')
        bot.register_next_step_handler(a, handle_voice)
    if message.text == 'Конвертировать в голос🎧':
        markup = telebot.types.InlineKeyboardMarkup()
        for voice in voices:
            button = telebot.types.InlineKeyboardButton(text=voice['title'], callback_data=voice['name'])
            markup.add(button)

        bot.reply_to(message, 'Привет! Я могу озвучить твое сообщение голосом. '
                              'Выбери голос, который хочешь использовать:', reply_markup=markup)


@bot.callback_query_handler(func=lambda call: True)
def voice_selection(call):


    selected_voice = call.data


    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                          text=f'Выбран голос: {selected_voice}')
    bot.send_message(chat_id=call.message.chat.id, text='Введите текст, который хотите озвучить:')

    bot.register_next_step_handler(call.message, get_text, selected_voice)

@bot.message_handler(content_types=['voice'])
def handle_voice(message):
    file_id = message.voice.file_id
    file_info = bot.get_file(file_id)
    file_path = file_info.file_path
    file_url = f'https://api.telegram.org/file/bot{bot_token}/{file_path}'

    r = requests.get(file_url, allow_redirects=True)
    open('voice.ogg', 'wb').write(r.content)

    response = requests.post(
        'https://stt.api.cloud.yandex.net/speech/v1/stt:recognize',
        headers={
            'Authorization': f'Api-Key {yandex_api_key}',
            'Content-Type': 'audio/ogg'
        },
        data=open('voice.ogg', 'rb').read()
    )

    if response.status_code == 200:
        text = response.json().get('result')
        bot.reply_to(message, f'Text: {text}')
    else:
        bot.reply_to(message, 'Что-то пошло не так! Попробуйте в следующий раз!')

    os.remove('voice.ogg')


def get_text(message, selected_voice):

    text = message.text


    url = f'https://tts.api.cloud.yandex.net/speech/v1/tts:synthesize?text={text}&lang=ru-RU&voice={selected_voice}'


    response = requests.post(url, headers={'Authorization': f'Api-Key {yandex_api_key}'})


    if response.ok:
        with open('voice.ogg', 'wb') as f:
            f.write(response.content)


        with open('voice.ogg', 'rb') as f:
            bot.send_voice(message.chat.id, f, reply_to_message_id=message.message_id)


        os.remove('voice.ogg')
    else:
        bot.reply_to(message, 'Ошибка при озвучивании сообщения.')


bot.polling()