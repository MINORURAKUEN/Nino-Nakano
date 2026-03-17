import os
import re
import subprocess
import time
from config import Config

def get_progress_bar(percentage: int) -> str:
    """Genera barra de progreso visual"""
    completed = int(percentage / 10)
    return "🟩" * completed + "⬜" * (10 - completed)

def cleanup_files(*files: str):
    """Limpia archivos temporales de forma segura"""
    for file_path in files:
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception:
            pass

def get_video_duration(file_path: str) -> float:
    """Obtiene duración del video con ffprobe"""
    try:
        cmd = [
            "ffprobe", "-v", "error", "-show_entries", 
            "format=duration", "-of", 
            "default=noprint_wrappers=1:nokey=1", file_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        return float(result.stdout.strip()) if result.stdout.strip() else 60.0
    except:
        return 60.0  # Fallback

def parse_ffmpeg_progress(line: str) -> float:
    """Parsea progreso de FFmpeg"""
    time_match = re.search(r"time=(\d{2}:\d{2}:\d{2}\.\d{2})", line)
    if time_match:
        h, m, s = map(float, time_match.group(1).split(':'))
        return h * 3600 + m * 60 + s
    return 0.0
