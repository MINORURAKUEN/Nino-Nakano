import asyncio
import os
import subprocess
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from config import Config
from utils import get_progress_bar, cleanup_files, get_video_duration, parse_ffmpeg_progress

app = Client("video_bot", api_id=Config.API_ID, api_hash=Config.API_HASH, bot_token=Config.BOT_TOKEN)

@app.on_message(filters.command("start"))
async def start_command(client, message):
    await message.reply(
        "🎬 **Video Converter Bot**\n\n"
        "📋 **Como usar:**\n"
        "1. Envía un video o responde `/dw` a un video\n"
        "2. Selecciona calidad\n"
        "3. Elige preset y formato\n"
        "4. ¡Listo! ✨",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📖 Ayuda", callback_data="help")]
        ])
    )

@app.on_message(filters.command("dw") & filters.reply)
async def dw_command(client, message):
    """Comando principal: responde a video"""
    reply_msg = message.reply_to_message
    media = reply_msg.video or reply_msg.document
    
    if not media:
        return await message.reply("❌ **Responde a un VIDEO o ARCHIVO video**")
    
    # Botones de calidad
    quality_buttons = [
        [InlineKeyboardButton(q["label"], callback_data=f"quality_{k}_{reply_msg.id}")]
        for k, q in Config.QUALITIES.items()
    ]
    
    await message.reply(
        "🎬 **Selecciona Calidad:**",
        reply_markup=InlineKeyboardMarkup(quality_buttons)
    )

@app.on_callback_query(filters.regex(r"^quality_(.+)_(\d+)$"))
async def select_preset(client: Client, callback: CallbackQuery):
    """Selecciona preset de velocidad"""
    _, quality_key, msg_id = callback.data.split("_", 2)
    
    preset_buttons = [
        [InlineKeyboardButton(p.upper(), callback_data=f"preset_{quality_key}_{p}_{msg_id}")]
        for p in Config.PRESETS
    ]
    
    await callback.message.edit(
        f"⚡ **Preset de Velocidad:**\n\n"
        f"**{Config.QUALITIES[quality_key]['label']}**",
        reply_markup=InlineKeyboardMarkup(preset_buttons)
    )

@app.on_callback_query(filters.regex(r"^preset_(.+)_(.+)_(\d+)$"))
async def select_format(client: Client, callback: CallbackQuery):
    """Selecciona formato final"""
    _, quality_key, preset, msg_id = callback.data.split("_", 3)
    
    format_buttons = [
        [
            InlineKeyboardButton("🎬 MP4", callback_data=f"convert_{quality_key}_{preset}_mp4_{msg_id}"),
            InlineKeyboardButton("🎞️ MKV", callback_data=f"convert_{quality_key}_{preset}_mkv_{msg_id}")
        ]
    ]
    
    await callback.message.edit(
        f"📁 **Formato Final:**\n\n"
        f"🎬 **{Config.QUALITIES[quality_key]['label']}**\n"
        f"⚡ **Preset:** `{preset.upper()}`",
        reply_markup=InlineKeyboardMarkup(format_buttons)
    )

@app.on_callback_query(filters.regex(r"^convert_(.+)_(.+)_(.+)_(\d+)$"))
async def convert_video(client: Client, callback: CallbackQuery):
    """Proceso principal de conversión"""
    try:
        _, quality_key, preset, fmt, msg_id_str = callback.data.split("_", 4)
        msg_id = int(msg_id_str)
        quality = Config.QUALITIES[quality_key]
        
        # Editar mensaje de estado
        status_msg = await callback.message.edit("⏳ **Descargando video...**")
        
        # Obtener mensaje original
        original_msg = await client.get_messages(callback.message.chat.id, msg_id)
        input_file = await client.download_media(original_msg)
        
        if not input_file or not os.path.exists(input_file):
            return await status_msg.edit("❌ **Error al descargar archivo**")
        
        output_file = f"converted_{int(time.time())}.{fmt}"
        
        # Obtener duración para progreso
        total_duration = get_video_duration(input_file)
        
        # Comando FFmpeg optimizado
        cmd = [
            "ffmpeg", "-i", input_file,
            "-vf", f"scale={quality['res']}:flags=lanczos",
            "-c:v", "libx264",
            "-preset", preset,
            "-b:v", quality['bitrate'],
            "-maxrate", f"{float(quality['bitrate'].replace('k','')) * 1.2}k",
            "-bufsize", f"{float(quality['bitrate'].replace('k','')) * 2}k",
            "-c:a", "aac", "-b:a", "128k",
            "-movflags", "+faststart",
            "-y", output_file
        ]
        
        # Ejecutar FFmpeg con progreso
        process = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            universal_newlines=True, bufsize=1
        )
        
        last_update = 0
        while process.poll() is None:
            line = process.stdout.readline()
            if line:
                current_time = parse_ffmpeg_progress(line)
                if total_duration > 0:
                    percentage = min(100, int((current_time / total_duration) * 100))
                    
                    if time.time() - last_update > 3:  # Actualizar cada 3s
                        bar = get_progress_bar(percentage)
                        await status_msg.edit(
                            f"⚙️ **Convirtiendo {quality['label']}**\n\n"
                            f"{bar} `{percentage}%`\n\n"
                            f"⚡ Preset: `{preset.upper()}`"
                        )
                        last_update = time.time()
        
        process.wait()
        
        # Verificar archivo de salida
        if not os.path.exists(output_file) or os.path.getsize(output_file) < 1024:
            raise Exception("FFmpeg falló")
        
        # Subir video convertido
        await status_msg.edit("📤 **Subiendo video convertido...**")
        
        await client.send_video(
            callback.message.chat.id,
            output_file,
            caption=f"✅ **¡Conversión Exitosa!**\n\n"
                   f"📺 **{quality['label']}**\n"
                   f"⚡ **Preset:** `{preset.upper()}`\n"
                   f"📁 **{fmt.upper()}`",
            reply_to_message_id=msg_id
        )
        
    except Exception as e:
        await callback.message.edit(f"❌ **Error:** `{str(e)[:100]}`")
    
    finally:
        # Limpieza automática
        cleanup_files(input_file, output_file)
        try:
            await callback.message.delete()
        except:
            pass

@app.on_callback_query(filters.regex(r"^help$"))
async def help_callback(client, callback):
    await callback.answer(
        "📋 Responde `/dw` a cualquier video!\n"
        "Selecciona calidad → preset → formato ✨",
        show_alert=True
    )

if __name__ == "__main__":
    print("🚀 Video Converter Bot iniciado!")
    print("📱 Comando: /dw (responder a video)")
    app.run()
