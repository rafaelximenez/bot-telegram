from telegram.ext import Updater, CommandHandler, MessageHandler, ConversationHandler, Filters, CallbackContext
from telegram.bot import Bot
from telegram import Update

from app.services.sentiment_analysis import GNlp
from app.services.ocr import GVision

import logging
import qrcode
import sys
import re
import os

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

SENTIMENT, QR = range(2)
TOKEN = os.environ.get("TELEGRAM_TOKEN")
MODE = os.environ.get("MODE")

class Telegram:
    def __init__(self):        
        self.bot = Bot(token=TOKEN)
        self.updater = Updater(TOKEN)

    #============================================================
    # OCR
    #============================================================
    def send_photo(self, update: Update, _: CallbackContext):
        file_id = update.message.photo[-1].file_id
        newFile = self.bot.getFile(file_id)
        
        filename = f'{os.getcwd()}/tmp/{file_id[0:8]}.jpg'
        newFile.download(filename)

        try:
            ocr = GVision()
            ocr_text, ocr_list = ocr.detect_text(filename)  
            update.message.reply_text(str(ocr_text))
        except:
            update.message.reply_text('Oooops! Eu não consegui converter essa imagem em texto')

    #============================================================
    # QR Code
    #============================================================
    def listen_qr(self, update: Update, _: CallbackContext):
        update.message.reply_text(
            "Me manda o texto para que eu gere seu QR."
        )

        return QR
    
    def generate_qr(self, update: Update, context: CallbackContext):
        if re.search('http', update.message.text):
            img = qrcode.make(update.message.text)
            filename = f'{os.getcwd()}/tmp/qr/image.jpg'
            img.save(filename)
            update.message.reply_photo(photo=open(filename, 'rb'))
        return ConversationHandler.END

    #============================================================
    # Análise de sentimentos
    #============================================================
    def listen_sentiment(self, update: Update, _: CallbackContext):
        update.message.reply_text(
            "Diga algo..."
        )

        return SENTIMENT

    def analysis_sentiment(self, update: Update, _: CallbackContext):
        sentiment_analysis = GNlp()
        score, magnitude = sentiment_analysis.analyze_feeling(update.message.text)
        
        '''
        Claramente positivo*	"score": 0.8, "magnitude": 3.0
        Claramente negativo*	"score": -0.6, "magnitude": 4.0
        Neutro	"score": 0.1, "magnitude": 0.0
        Misto	"score": 0.0, "magnitude": 4.0
        '''
        if score >= 0.4 and score <= 1:
            update.message.reply_text('Sentimento positivo!')
        elif score >= -0.3 and score <= 0.3:
            update.message.reply_text('Sentimento neutro!')
        elif score >= -1 and score <= -0.4:
            update.message.reply_text('Sentimento negativo!')
        else:
            update.message.reply_text(f'Score: {round(score, 2)} - Magnitude: {round(magnitude, 2)}')
        return ConversationHandler.END

    #============================================================
    # Runtime
    #============================================================
    def main(self) -> None:    
        dispatcher = self.updater.dispatcher

        conv_qr = ConversationHandler(
            entry_points=[CommandHandler("qr", self.listen_qr)],
            states={
                QR: [MessageHandler(Filters.text, self.generate_qr)],
            },
            fallbacks=[],   
        )

        conv_sentiment = ConversationHandler(
            entry_points=[CommandHandler("sentimento", self.listen_sentiment)],
            states={
                SENTIMENT: [MessageHandler(Filters.text, self.analysis_sentiment)],
            },
            fallbacks=[],   
        )

        dispatcher.add_handler(conv_qr)
        dispatcher.add_handler(conv_sentiment)

        dispatcher.add_handler(MessageHandler(Filters.photo, self.send_photo))
        
        if MODE == "DEV":
            self.updater.start_polling()
            self.updater.idle()
        elif MODE == "PROD":
            PORT = int(os.environ.get("PORT", "8443"))
            HEROKU_APP_NAME = os.environ.get("HEROKU_APP_NAME")
            self.updater.start_webhook(listen="0.0.0.0",
                                port=PORT,
                                url_path=TOKEN)
            self.updater.bot.set_webhook("https://{}.herokuapp.com/{}".format(HEROKU_APP_NAME, TOKEN))
        else:
            logger.error("No MODE specified!")
            sys.exit(1)