import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    API_ID = int(os.getenv("API_ID"))
    API_HASH = os.getenv("API_HASH")
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    
    # 🎬 Calidades Video
    QUALITIES = {
        "240p": {"res": "426:240", "bitrate": "400k", "label": "📱 240p"},
        "360p": {"res": "640:360", "bitrate": "800k", "label": "📱 360p"},
        "480p": {"res": "854:480", "bitrate": "1500k", "label": "💻 480p"},
        "720p": {"res": "1280:720", "bitrate": "2800k", "label": "💻 720p"},
        "1080p": {"res": "1920:1080", "bitrate": "5000k", "label": "🎬 1080p"}
    }
    
    PRESETS = ["ultrafast", "superfast", "veryfast", "faster", "fast"]
    FORMATS = ["mp4", "mkv"]
    
    # 🔥 Estilos Subtítulos
    SUBTITLE_STYLES = {
        "default": {
            "fontsize": "24", "fontcolor": "white",
            "bordercolor": "black", "borderstyle": "3",
            "backcolor": "0x00000099"
        },
        "anime": {
            "fontsize": "28", "fontcolor": "white",
            "bordercolor": "black", "borderstyle": "4",
            "backcolor": "0x000000AA"
        },
        "movie": {
            "fontsize": "32", "fontcolor": "yellow",
            "bordercolor": "black", "borderstyle": "3",
            "backcolor": "0x000000BB"
        }
    }
