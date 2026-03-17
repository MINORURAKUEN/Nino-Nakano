import os
import subprocess
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler

# Reemplaza esto con tu token
TOKEN = 'TU_TOKEN_AQUI'

# Estados de la conversación
ESPERANDO_VIDEO, ESPERANDO_SUBTITULO = range(2)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "¡Hola! Soy tu bot de procesamiento de video.\n"
        "Envíame un video para empezar (máximo 20MB)."
    )
    return ESPERANDO_VIDEO

async def recibir_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Obtener el archivo de video
    video = update.message.video or update.message.document
    
    if not video:
        await update.message.reply_text("Por favor, envíame un archivo de video válido.")
        return ESPERANDO_VIDEO

    file = await context.bot.get_file(video.file_id)
    video_path = f"input_{update.message.chat_id}.mp4"
    await file.download_to_drive(video_path)
    
    # Guardar la ruta en los datos del usuario
    context.user_data['video_path'] = video_path

    await update.message.reply_text(
        "¡Video recibido! 🎬\n"
        "Ahora envíame el archivo de subtítulos (.srt).\n"
        "Si solo quieres comprimir el video sin subtítulos, envía /omitir"
    )
    return ESPERANDO_SUBTITULO

async def procesar_video(update: Update, context: ContextTypes.DEFAULT_TYPE, subs_path=None):
    chat_id = update.message.chat_id
    video_path = context.user_data.get('video_path')
    output_path = f"output_{chat_id}.mp4"

    await update.message.reply_text("⏳ Procesando... Esto puede tardar unos minutos. ¡Paciencia!")

    # Construir el comando de FFmpeg
    # -vcodec libx264 -crf 28: Comprime el video (mayor CRF = más compresión, menor calidad)
    # -preset fast: Velocidad de procesamiento
    comando = ['ffmpeg', '-y', '-i', video_path]

    if subs_path:
        # Nota: En Windows, las barras invertidas en la ruta del subtítulo pueden causar errores en FFmpeg.
        # Nos aseguramos de usar barras normales o escapar la ruta si es necesario.
        subs_path_formateado = subs_path.replace('\\', '/')
        comando.extend(['-vf', f"subtitles={subs_path_formateado}"])
    
    comando.extend(['-c:v', 'libx264', '-crf', '28', '-preset', 'fast', '-c:a', 'aac', '-b:a', '128k', output_path])

    try:
        # Ejecutar FFmpeg
        subprocess.run(comando, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Enviar el video resultante
        await update.message.reply_text("✅ ¡Proceso terminado! Subiendo el video...")
        with open(output_path, 'rb') as video_file:
            await context.bot.send_video(chat_id=chat_id, video=video_file)
            
    except subprocess.CalledProcessError as e:
        await update.message.reply_text(f"❌ Error al procesar el video: {e}")
    finally:
        # Limpieza de archivos temporales
        if os.path.exists(video_path): os.remove(video_path)
        if os.path.exists(output_path): os.remove(output_path)
        if subs_path and os.path.exists(subs_path): os.remove(subs_path)

    return ConversationHandler.END

async def recibir_subtitulos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    document = update.message.document
    if not document.file_name.endswith('.srt'):
        await update.message.reply_text("Por favor, envía un archivo con extensión .srt")
        return ESPERANDO_SUBTITULO

    file = await context.bot.get_file(document.file_id)
    subs_path = f"subs_{update.message.chat_id}.srt"
    await file.download_to_drive(subs_path)

    # Llamar a la función de procesamiento con subtítulos
    return await procesar_video(update, context, subs_path)

async def omitir_subtitulos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Llamar a la función de procesamiento sin subtítulos
    return await procesar_video(update, context, subs_path=None)

async def cancelar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Operación cancelada. Envía /start para empezar de nuevo.")
    return ConversationHandler.END

def main():
    app = Application.builder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            ESPERANDO_VIDEO: [MessageHandler(filters.VIDEO | filters.Document.VIDEO, recibir_video)],
            ESPERANDO_SUBTITULO: [
                MessageHandler(filters.Document.ALL, recibir_subtitulos),
                CommandHandler('omitir', omitir_subtitulos)
            ]
        },
        fallbacks=[CommandHandler('cancelar', cancelar)]
    )

    app.add_handler(conv_handler)
    print("Bot en ejecución...")
    app.run_polling()

if __name__ == '__main__':
    main()
      
