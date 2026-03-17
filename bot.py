import asyncio
import os
import subprocess
import time
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from config import Config
from utils import *

app = Client("super_video_bot", api_id=Config.API_ID, api_hash=Config.API_HASH, bot_token=Config.BOT_TOKEN)

@app.on_message(filters.command("start"))
async def start(client, message):
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("🎬 Convertir Video", callback_data="menu_convert")],
        [InlineKeyboardButton("🔥 Quemar Subtítulos", callback_data="menu_subs")],
        [InlineKeyboardButton("📖 Ayuda", callback_data="help")]
    ])
    
    await message.reply(
        "🚀 **Super Video Bot** *(Conversión + Subtítulos)*\n\n"
        "🎬 **`/dw`** - Convertir video (responde a video)\n"
        "🔥 **`/subs`** - Quemar subtítulos (video + .srt)\n\n"
        "**Soporta:** MP4/MKV | 240p-1080p | SRT/VTT/ASS",
        reply_markup=kb
    )

# 🎬 CONVERSIÓN VIDEO NORMAL
@app.on_message(filters.command("dw") & filters.reply)
async def dw_command(client, message):
    reply_msg = message.reply_to_message
    media = reply_msg.video or reply_msg.document
    
    if not media:
        return await message.reply("❌ **Responde a un VIDEO**")
    
    quality_buttons = [
        [InlineKeyboardButton(q["label"], callback_data=f"quality_{k}_{reply_msg.id}_normal")]
        for k, q in Config.QUALITIES.items()
    ]
    
    await message.reply("🎬 **Selecciona Calidad:**", reply_markup=InlineKeyboardMarkup(quality_buttons))

# 🔥 SUBTÍTULOS QUEMADOS
@app.on_message(filters.command("subs"))
async def subs_command(client, message):
    if not message.reply_to_message:
        return await message.reply("❌ **Responde a un VIDEO**")
    
    video_msg = message.reply_to_message
    if not (video_msg.video or video_msg.document):
        return await message.reply("❌ **Responde a un VIDEO**")
    
    # Verificar subtítulo adjunto
    subtitle_file = None
    if message.document:
        ext = message.document.file_name.lower() if message.document.file_name else ""
        if ext in ['.srt', '.vtt', '.ass', '.ssa']:
            subtitle_file = await message.download()
    
    if not subtitle_file:
        return await message.reply(
            "❌ **Adjunta subtítulo (.srt/.vtt/.ass/.ssa)**\n\n"
            "📝 **Ejemplo:**\n"
            "• Video → `/subs` + archivo.srt"
        )
    
    # Botones calidad para subtítulos
    sub_buttons = [
        [InlineKeyboardButton(f"🔥 {q['label']}", callback_data=f"subs_{k}_{video_msg.id}_{subtitle_file}")]
        for k, q in Config.QUALITIES.items()
    ]
    
    await message.reply(
        f"✅ **Subtítulo:** `{os.path.basename(subtitle_file)}`\n\n"
        "🔥 **Selecciona Calidad:**",
        reply_markup=InlineKeyboardMarkup(sub_buttons)
    )

# 🎯 CALLBACKS UNIFICADOS
@app.on_callback_query(filters.regex(r"^(quality|subs)_(.+)_(\d+)(?:_(.+))?$"))
async def handle_selection(client: Client, callback: CallbackQuery):
    data = callback.data.split("_")
    action, quality_key, msg_id = data[0], data[2], int(data[3])
    
    if action == "quality":  # 🎬 Conversión normal
        preset_buttons = [
            [InlineKeyboardButton(p.upper(), callback_data=f"preset_{quality_key}_{Config.PRESETS[0]}_{msg_id}_normal")]
            for p in Config.PRESETS[:3]  # Solo presets rápidos
        ] + [[InlineKeyboardButton("🚀 Rápido", callback_data=f"preset_{quality_key}_fast_{msg_id}_normal")]]
        
        await callback.message.edit(
            f"⚡ **Preset:**\n\n**{Config.QUALITIES[quality_key]['label']}**",
            reply_markup=InlineKeyboardMarkup(preset_buttons)
        )
    
    elif action == "subs":  # 🔥 Subtítulos
        subtitle_path = data[4]
        await convert_with_subtitles(client, callback, quality_key, msg_id, subtitle_path)

@app.on_callback_query(filters.regex(r"^preset_(.+)_(.+)_(\d+)_normal$"))
async def select_format(client: Client, callback: CallbackQuery):
    _, quality_key, preset, msg_id = callback.data.split("_", 3)
    
    format_buttons = [
        [
            InlineKeyboardButton("🎬 MP4", callback_data=f"convert_{quality_key}_{preset}_mp4_{msg_id}_normal"),
            InlineKeyboardButton("🎞 MKV", callback_data=f"convert_{quality_key}_{preset}_mkv_{msg_id}_normal")
        ]
    ]
    
    await callback.message.edit(
        f"📁 **Formato:**\n\n🎬 **{Config.QUALITIES[quality_key]['label']}** | `{preset.upper()}`",
        reply_markup=InlineKeyboardMarkup(format_buttons)
    )

@app.on_callback_query(filters.regex(r"^convert_(.+)_(.+)_(.+)_(\d+)_normal$"))
async def convert_normal(client: Client, callback: CallbackQuery):
    await convert_video(client, callback, is_subtitle=False)

async def convert_video(client: Client, callback: CallbackQuery, is_subtitle: bool = False):
    """🎬 Conversión genérica (normal o subtítulos)"""
    try:
        data = callback.data.split("_")
        quality_key, preset, fmt, msg_id_str = data[1], data[2], data[3], int(data[4])
        quality = Config.QUALITIES[quality_key]
        
        status_msg = await callback.message.edit("⏳ **Descargando...**")
        msg = await client.get_messages(callback.message.chat.id, msg_id_str)
        input_file = await client.download_media(msg)
        
        if not input_file:
            return await status_msg.edit("❌ **Error descarga**")
        
        output_file = f"out_{int(time.time())}.{fmt}"
        total_duration = get_video_duration(input_file)
        
        # 🎬 Comando base
        cmd = [
            "ffmpeg", "-i", input_file,
            "-vf", f"scale={quality['res']}:flags=lanczos",
            "-c:v", "libx264", "-preset", preset,
            "-b:v", quality['bitrate'],
            "-c:a", "aac", "-b:a", "128k",
            "-movflags", "+faststart", "-y", output_file
        ]
        
        # 🔥 Si es subtítulos, agregar filtro
        if is_subtitle:
            subtitle_path = data[5]  # Desde callback data
            subtitle_filter = build_subtitle_filter(subtitle_path)
            cmd[2] = f"scale={quality['res']}:flags=lanczos,{subtitle_filter}"
        
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
        
        last_update = 0
        while process.poll() is None:
            line = process.stdout.readline()
            if line:
                current_time = parse_ffmpeg_progress(line)
                percentage = min(100, int((current_time / total_duration) * 100))
                
                if time.time() - last_update > 2.5:
                    bar = get_progress_bar(percentage)
                    mode = "🔥 Subtítulos" if is_subtitle else f"⚙️ {Config.QUALITIES[quality_key]['label']}"
                    await status_msg.edit(f"{mode}\n\n{bar} `{percentage}%` | `{preset.upper()}`")
                    last_update = time.time()
        
        process.wait()
        
        if os.path.exists(output_file) and os.path.getsize(output_file) > 1024:
            await status_msg.edit("📤 **Subiendo...**")
            
            caption = f"✅ **Listo!**\n\n"
            if is_subtitle:
                caption += f"🔥 **{quality['label']}** + Subtítulos\n📄 `{os.path.basename(subtitle_path)}`"
            else:
                caption += f"🎬 **{quality['label']}** | `{preset.upper()}` | **{fmt.upper()}**"
            
            await client.send_video(
                callback.message.chat.id, output_file, caption=caption,
                reply_to_message_id=msg_id_str
            )
        else:
            raise Exception("FFmpeg error")
            
    except Exception as e:
        await callback.message.edit(f"❌ **Error:** `{str(e)[:100]}`")
    
    finally:
        cleanup_files(input_file, output_file)
        try:
            await callback.message.delete()
        except:
            pass

@app.on_callback_query(filters.regex(r"^help$"))
async def help_callback(client, callback):
    await callback.answer(
        "**Comandos:**\n"
        "• `/dw` + video = Convertir\n"
        "• `/subs` + video + .srt = Subtítulos\n\n"
        "**Formatos:** SRT/VTT/ASS/MP4/MKV",
        show_alert=True
    )

if __name__ == "__main__":
    print("🚀 **Super Video Bot** iniciado!")
    print("🎬 /dw - Convertir | 🔥 /subs - Subtítulos")
    app.run()
