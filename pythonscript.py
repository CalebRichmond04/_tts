import time
import difflib
import re
from pathlib import Path
from collections import deque
import pythoncom
import pyttsx3

FILE_PATH = Path("retroarch.log")
KEYWORD = "achievement"
CHECK_INTERVAL = 3  # seconds
CACHE_SECONDS = 30  # allow repeats after 30 seconds

# ---------------- TTS ----------------
def speak(text):
    """Fully reinitialize COM and engine each time"""
    try:
        # Initialize COM for this thread (Windows specific)
        pythoncom.CoInitialize()
        
        engine = pyttsx3.init()
        engine.setProperty("rate", 175)
        engine.say(text)
        engine.runAndWait()
        
        # Force cleanup
        engine.stop()
        del engine
        
        # Uninitialize COM
        pythoncom.CoUninitialize()
    except Exception as e:
        print(f"TTS Error: {e}")
        try:
            pythoncom.CoUninitialize()
        except:
            pass

# ---------------- PARSE ACHIEVEMENT ----------------
def extract_achievement_name(line):
    """Extract achievement name from log line"""
    # Pattern: [INFO] [RCHEEVOS] Awarding achievement 458335: A Straight 30 Meter Dive
    match = re.search(r'achievement\s+\d+:\s*(.+)', line, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return None

# ---------------- FILE READ ----------------
def read_lines():
    try:
        return FILE_PATH.read_text(
            encoding="utf-8",
            errors="ignore"
        ).splitlines()
    except FileNotFoundError:
        return []

# ---------------- WATCH ----------------
def watch_file():
    previous_lines = read_lines()

    # stores (timestamp, achievement_name)
    recent_spoken = deque()

    while True:
        time.sleep(CHECK_INTERVAL)
        current_lines = read_lines()
        now = time.time()

        # Remove expired cache entries
        while recent_spoken and now - recent_spoken[0][0] > CACHE_SECONDS:
            recent_spoken.popleft()

        recently_spoken_names = {name for _, name in recent_spoken}

        diff = difflib.ndiff(previous_lines, current_lines)

        for line in diff:
            if line.startswith("+ "):
                text = line[2:]

                if KEYWORD.lower() in text.lower():
                    achievement_name = extract_achievement_name(text)
                    
                    if achievement_name and achievement_name not in recently_spoken_names:
                        print(f"Achievement detected: {achievement_name}")
                        
                        # Speak with prefix
                        announcement = f"Achievement unlocked: {achievement_name}"
                        speak(announcement)
                        
                        recent_spoken.append((now, achievement_name))

        previous_lines = current_lines


if __name__ == "__main__":
    watch_file()