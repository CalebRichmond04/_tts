import time
import re
from pathlib import Path
import pyttsx3
import threading
import requests

import wled_presets

# ============================================================================
# CONFIGURATION - Edit these settings
# ============================================================================

CELEBRATION_DURATION = 5  # seconds

# WLED fallback state (static red)
WLED_IP = "192.168.1.124"
STATIC_RED = [255, 0, 0]

# TTS Settings
TTS_VOICE_INDEX = 1
TTS_RATE = 175
TTS_VOLUME = 1.0

# Monitoring Settings
CHECK_INTERVAL = 2
DEBUG_MODE = False

# ============================================================================
# END CONFIGURATION
# ============================================================================

class AchievementAnnouncer:
    def __init__(self, script_dir):
        self.script_dir = Path(script_dir)
        self.log_file = self.script_dir.parent / "logs" / "retroarch.log"
        self.announced_achievements = set()
        self.setup_tts()

    def setup_tts(self):
        try:
            self.tts_engine = pyttsx3.init()
            voices = self.tts_engine.getProperty('voices')

            if DEBUG_MODE:
                print("\n=== Available TTS Voices ===")
                for i, voice in enumerate(voices):
                    print(f"{i}: {voice.name}")
                print("============================\n")

            if TTS_VOICE_INDEX < len(voices):
                self.tts_engine.setProperty('voice', voices[TTS_VOICE_INDEX].id)
                print(f"Using voice: {voices[TTS_VOICE_INDEX].name}")

            self.tts_engine.setProperty('rate', TTS_RATE)
            self.tts_engine.setProperty('volume', TTS_VOLUME)

        except Exception as e:
            print(f"TTS Setup Error: {e}")
            self.tts_engine = None

    def set_static_red(self):
        payload = {
            "on": True,
            "seg": [{
                "col": [STATIC_RED],
                "fx": 0,
                "sx": 128,
                "ix": 128
            }]
        }

        try:
            requests.post(f"http://{WLED_IP}/json/state", json=payload, timeout=1)
        except Exception as e:
            if DEBUG_MODE:
                print(f"Failed to set static red: {e}")

    def celebrate_achievement(self):
        wled_presets.start_preset("dual_chase_bounce")
        time.sleep(CELEBRATION_DURATION)
        wled_presets.stop_preset()
        self.set_static_red()

    def announce(self, achievement_name):
        message = f"Achievement unlocked: {achievement_name}"
        print(message)

        wled_thread = threading.Thread(target=self.celebrate_achievement)
        wled_thread.daemon = True
        wled_thread.start()

        if self.tts_engine:
            try:
                engine = pyttsx3.init()
                voices = engine.getProperty('voices')

                if TTS_VOICE_INDEX < len(voices):
                    engine.setProperty('voice', voices[TTS_VOICE_INDEX].id)

                engine.setProperty('rate', TTS_RATE)
                engine.setProperty('volume', TTS_VOLUME)

                engine.say(message)
                engine.runAndWait()
                engine.stop()

            except Exception as e:
                print(f"TTS Error: {e}")

    def parse_achievement_name(self, lines, awarded_line_index):
        awarded_match = re.search(r'Achievement (\d+) awarded', lines[awarded_line_index])
        if not awarded_match:
            return None, None

        achievement_id = awarded_match.group(1)

        for i in range(max(0, awarded_line_index - 5), awarded_line_index):
            if f'Awarding achievement {achievement_id}:' in lines[i]:
                name_match = re.search(rf'Awarding achievement {achievement_id}: (.+)$', lines[i])
                if name_match:
                    return achievement_id, name_match.group(1).strip()

        return achievement_id, None

    def scan_log_for_achievements(self):
        try:
            if not self.log_file.exists():
                if DEBUG_MODE:
                    print(f"Log file not found: {self.log_file}")
                return

            with open(self.log_file, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.read().split('\n')

            for line_index, line in enumerate(lines):
                if 'awarded' in line and '[RCHEEVOS]' in line:
                    achievement_id, achievement_name = self.parse_achievement_name(lines, line_index)

                    if achievement_id and achievement_name:
                        unique_id = f"{self.log_file.name}:{achievement_id}"

                        if unique_id not in self.announced_achievements:
                            self.announce(achievement_name)
                            self.announced_achievements.add(unique_id)

                            if DEBUG_MODE:
                                print(f"Announced achievement {achievement_id}")

        except Exception as e:
            print(f"Error scanning file: {e}")

    def monitor_log(self):
        print("=" * 60)
        print("RetroArch Achievement Announcer (Custom WLED Presets)")
        print("=" * 60)
        print(f"Log location: {self.log_file}")
        print(f"TTS Voice Index: {TTS_VOICE_INDEX}")
        print(f"Scan interval: {CHECK_INTERVAL}s")
        print(f"Debug mode: {'ON' if DEBUG_MODE else 'OFF'}")
        print("=" * 60)
        print()

        if not self.log_file.exists():
            print("Waiting for RetroArch log file...")
            print(f"Looking for: {self.log_file}")
        else:
            print("Log file found!")

        print("\nMonitoring for achievements...\n")

        while True:
            try:
                self.scan_log_for_achievements()
                time.sleep(CHECK_INTERVAL)

            except KeyboardInterrupt:
                print("\nStopping Achievement Announcer...")
                break

            except Exception as e:
                print(f"Error: {e}")
                time.sleep(CHECK_INTERVAL)


def main():
    script_dir = Path(__file__).parent.absolute()
    announcer = AchievementAnnouncer(script_dir)
    announcer.monitor_log()


if __name__ == "__main__":
    main()
