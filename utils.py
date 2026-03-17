import os
import re
import subprocess
import time
from config import Config

def get_progress_bar(percentage: int) -> str:
    completed = int(percentage / 10)
    return "🟩" * completed + "⬜" * (10 - completed)

def cleanup_files(*files: str):
    for file_path in files:
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except:
            pass

def get_video_duration(file_path: str) -> float:
    try:
        cmd = ["ffprobe", "-v", "error", "-show_entries", 
               "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", file_path]
        result = subprocess.run(cmd, capture_output=True, text=True)
        return float(result.stdout.strip()) if result.stdout.strip() else 60.0
    except:
        return 60.0

def parse_ffmpeg_progress(line: str) -> float:
    time_match = re.search(r"time=(\d{2}:\d{2}:\d{2}\.\d{2})", line)
    if time_match:
        h, m, s = map(float, time_match.group(1).split(':'))
        return h * 3600 + m * 60 + s
    return 0.0

def build_subtitle_filter(subtitle_file: str, style: str = "default") -> str:
    """🔥 Filtro subtítulos quemados"""
    style_config = Config.SUBTITLE_STYLES.get(style, Config.SUBTITLE_STYLES["default"])
    
    filter_str = (
        f"subtitles='{subtitle_file.replace('\\'','\\\\\\'')}':"
        f"force_style='FontSize={style_config['fontsize']},"
        f"PrimaryColour=&H{style_config['fontcolor'].replace('0x','')},"
        f"OutlineColour=&H{style_config['bordercolor'].replace('0x','')},"
        f"BackColour=&H{style_config['backcolor'].replace('0x','')},"
        f"BorderStyle={style_config['borderstyle']},"
        f"Outline=2,MarginV=60'"
    )
    return filter_str
