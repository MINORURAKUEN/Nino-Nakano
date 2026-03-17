import os
import subprocess
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

load_dotenv()
TOKEN = os.getenv('TELEGRAM_TOKEN')

# --- Lógica de Extracción de Pistas (Audio/Subs) ---
def get_streams_info(file_path):
    # Extraemos audios
    cmd_audio = ['ffprobe', '-v', '0', '-select_streams', 'a', '-show_entries', 'stream=index:stream_tags=language', '-of', 'csv=p=0', file_path]
    audios = subprocess.run(cmd_audio, capture_output=True, text=True).stdout.strip().split('\n')
    
    # Extraemos subtítulos
    cmd_subs = ['ffprobe', '-v', '0', '-select_streams', 's', '-show_entries', 'stream=index:stream_tags=language', '-of', 'csv=p=0', file_path]
    subs = subprocess.run(cmd_subs, capture_output=True, text=True).stdout.strip().split('\n')
    
    return [a for a in audios if a], [s for s in subs if s]

# --- Comando /dw2 ---
async def comando_dw2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message:
        return # Solo funciona respondiendo a un video

    video_msg = update.message.reply_to_message
    archivo_tg = video_msg.video or video_msg.document
    
    if not archivo_tg: return

    # 1. Descarga silenciosa
    file = await context.bot.get_file(archivo_tg.file_id)
    temp_path = f"dw_{update.effective_user.id}.mp4"
    await file.download_to_drive(temp_path)

    # 2. Obtener info de pistas
    audios, subs = get_streams_info(temp_path)
    audio_txt = "\n".join([f"{i}. 🌍 {a}" for i, a in enumerate(audios)]) if audios else "(ninguno)"
    subs_txt = "\n".join([f"{i}. 📝 {s}" for i, s in enumerate(subs)]) if subs else "(ninguna)"

    # 3. Construir Menú de Botones
    keyboard = [
        [
            InlineKeyboardButton("⚡ 1080p CR", callback_data="1080_cr"),
            InlineKeyboardButton("⚡ 1080p YA", callback_data="1080_ya"),
        ],
        [
            InlineKeyboardButton("⚡ 720p HD", callback_data="720_hd"),
            InlineKeyboardButton("⚡ 720p HDL", callback_data="720_hdl"),
        ],
        [InlineKeyboardButton("❌ Cancelar", callback_data="cancelar")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # 4. Enviar respuesta estilo captura
    texto = (
        f"📊 <b>Media Info</b>\n"
        f"📦 <code>{archivo_tg.file_name or 'video.mp4'}</code>\n\n"
        f"🎵 <b>Pistas de audio:</b>\n{audio_txt}\n\n"
        f"📝 <b>Subtítulos:</b>\n{subs_txt}\n\n"
        f"🎬 <b>Paso 1/5 — Selecciona la calidad:</b>"
    )
    
    await update.message.reply_html(texto, reply_markup=reply_markup)
    # Guardamos la ruta en context para el siguiente paso
    context.user_data['temp_video'] = temp_path

# --- Manejador de Botones ---
async def botones_calidad(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    if data == "cancelar":
        await query.edit_message_text("❌ Proceso cancelado.")
        # Borrar archivo temporal
        return

    # Aquí pasaría al Paso 2 (Elegir audio o quemar subs)
    await query.edit_message_text(f"Has seleccionado: {data}. \n⏳ Iniciando codificación...")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("dw2", comando_dw2))
    app.add_handler(CallbackQueryHandler(botones_calidad))
    app.run_polling()

if __name__ == "__main__":
    main()

