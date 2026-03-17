import os
import subprocess
from dotenv import load_dotenv
from telegraph import Telegraph
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Cargar credenciales
load_dotenv()
TOKEN = os.getenv('TELEGRAM_TOKEN')

# Configurar Telegraph
telegraph = Telegraph()
telegraph.create_account(short_name='MediaInfoBot')

def subir_a_graph(reporte_texto, nombre):
    html = f"<h4>Reporte: {nombre}</h4><pre>{reporte_texto}</pre>"
    response = telegraph.create_page(title='MediaInfo', html_content=html)
    return f"https://graph.org/{response['path']}"

async def obtener_mediainfo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Solo actuar si es una respuesta a un video/archivo
    if not update.message.reply_to_message:
        return

    msg_reply = update.message.reply_to_message
    archivo_tg = msg_reply.video or msg_reply.document or msg_reply.animation
    
    if not archivo_tg:
        return

    # Definir rutas
    file_id = archivo_tg.file_id
    nombre = getattr(archivo_tg, 'file_name', "video.mp4")
    temp_path = f"temp_{file_id}"

    try:
        # Descarga silenciosa
        file = await context.bot.get_file(file_id)
        await file.download_to_drive(temp_path)

        # Ejecutar MediaInfo de forma directa
        resultado = subprocess.run(['mediainfo', '-f', temp_path], capture_output=True, text=True, encoding='utf-8')
        
        if resultado.returncode == 0:
            link_graph = subir_a_graph(resultado.stdout, nombre)
            # Respuesta final directa
            await update.message.reply_html(
                f"<b>➲ Link :</b> {link_graph}", 
                disable_web_page_preview=False
            )

    except Exception:
        pass # Silencio en caso de error para mantener la limpieza
    
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

def main():
    if not TOKEN: return
    
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("mi", obtener_mediainfo))
    app.run_polling()

if __name__ == "__main__":
    main()
  
