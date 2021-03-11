
import telegram
import os

class Telegram:
    def __init__(self):
        self.token = os.environ['TELEGRAM_TOKEN']
        self.chat_id = os.environ['TELEGRAM_CHAT_ID']

        self.bot = telegram.Bot(token=self.token)

    def send_message(self, message):        
        self.bot.send_message(text=message, chat_id=self.chat_id)

if __name__ == '__main__':
    telegram = Telegram()
    telegram.send_message('Ola bundão')
