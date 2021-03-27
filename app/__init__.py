import os
import re
import sys
import logging
import qrcode

from .helpers import ocr
from .helpers import sentiment_analysis
from telegram import Update, ReplyKeyboardMarkup
from telegram.bot import Bot
from telegram.ext import Updater, CommandHandler, MessageHandler, ConversationHandler, Filters, CallbackContext

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

SENTIMENT, QR = range(2)

mode = os.getenv("MODE")
TOKEN = os.getenv("TELEGRAM_TOKEN")

def send_photo(update: Update, _: CallbackContext):
    bot = Bot(token=TOKEN)
    file_id = update.message.photo[-1].file_id
    newFile = bot.getFile(file_id)
    
    filename = 'tmp/{}.jpg'.format(file_id[0:8])
    newFile.download(filename)

    try:
        ocr_text, ocr_list = ocr.detect_text(filename)    
        update.message.reply_text(str(ocr_text))
    except:
        update.message.reply_text('Oooops! Eu não consegui converter essa imagem em texto')

def listen_qr(update: Update, _: CallbackContext):
    update.message.reply_text(
        "Me manda o texto para que eu gere seu QR."
    )

    return QR

def listen_sentiment(update: Update, _: CallbackContext):
    update.message.reply_text(
        "Diga algo..."
    )

    return SENTIMENT

def generate_qr(update: Update, context: CallbackContext):
    if re.search('http', update.message.text):
        img = qrcode.make(update.message.text)
        filename = 'tmp/qr/image.jpg'
        img.save(filename)
        update.message.reply_photo(photo=open(filename, 'rb'))
    return ConversationHandler.END

def analysis_sentiment(update: Update, _: CallbackContext):
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

def main() -> None:
    updater = Updater(TOKEN)
    
    dispatcher = updater.dispatcher

    conv_qr = ConversationHandler(
        entry_points=[CommandHandler("qr", listen_qr)],
        states={
            QR: [MessageHandler(Filters.text, generate_qr)],
        },
        fallbacks=[],   
    )

    conv_sentiment = ConversationHandler(
        entry_points=[CommandHandler("sentimento", listen_sentiment)],
        states={
            SENTIMENT: [MessageHandler(Filters.text, analysis_sentiment)],
        },
        fallbacks=[],   
    )

    dispatcher.add_handler(conv_qr)
    dispatcher.add_handler(conv_sentiment)

    dispatcher.add_handler(MessageHandler(Filters.photo, send_photo))
    
    if mode == "DEV":
        updater.start_polling()
        updater.idle()
    elif mode == "PROD":
        PORT = int(os.environ.get("PORT", "8443"))
        HEROKU_APP_NAME = os.environ.get("HEROKU_APP_NAME")
        updater.start_webhook(listen="0.0.0.0",
                              port=PORT,
                              url_path=TOKEN)
        updater.bot.set_webhook("https://{}.herokuapp.com/{}".format(HEROKU_APP_NAME, TOKEN))
    else:
        logger.error("No MODE specified!")
        sys.exit(1)