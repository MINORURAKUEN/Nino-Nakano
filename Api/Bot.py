import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Cargamos las variables del archivo .env
load_dotenv()
TOKEN = os.getenv('TELEGRAM_TOKEN')

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Bot conectado y listo para recibir videos.")

if __name__ == '__main__':
    if not TOKEN:
        print("Error: No se encontró el TOKEN en el archivo .env")
    else:
        app = Application.builder().token(TOKEN).build()
        app.add_handler(CommandHandler("start", start))
        print("Bot iniciado...")
        app.run_polling()
      
