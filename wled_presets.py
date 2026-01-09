import time
import random
import requests
import threading

# ================= DEVICE CONFIG =================
# Add your WLED devices here with their IP addresses and number of LEDs
# IP = number of LEDs in the strip
WLED_DEVICES = {
    "192.168.1.124": 209,  # Device 1
    "192.168.1.69": 174    # Device 2
}

# Global flag used to stop a running preset
STOP_EFFECT = False

# ===============================================
# ====== HELPER FUNCTIONS FOR LED CONTROL ======
# ===============================================

def set_leds(ip, leds):
    """
    Send a frame of LED data to a single WLED device.
    - ip: IP address of the WLED device
    - leds: List of [R,G,B] values for each LED
    """
    payload = {"on": True, "seg": {"i": leds}}
    try:
        requests.post(f"http://{ip}/json/state", json=payload, timeout=0.3)
    except:
        pass

def set_all_devices(frame_map):
    """
    Send a frame of LED data to all devices defined in WLED_DEVICES.
    - frame_map: Dictionary of {ip: leds} where leds is a list of [R,G,B] values
    """
    for ip, leds in frame_map.items():
        set_leds(ip, leds)

# =========================================
# ====== PRESETS / EFFECT FUNCTIONS =======
# =========================================

def dual_chase_bounce(
    move_speed=10,
    frame_delay=0
):
    """
    Dual chase effect (game show theme):
    - Two lines start at opposite ends of the strip and move toward each other, then bounce.
    - Colors cycle through gold, white, blue, green.
    - move_speed: number of LEDs the lines move per frame
    - frame_delay: delay between frames (0 = as fast as possible)
    - brightness: scales the intensity of LEDs (0.0 = off, 1.0 = full)
    """
    # ===== CONFIGURABLE COLORS =====
    colors = [
        [255, 215, 0],  # Gold
        [255, 255, 255],# White
        [0, 0, 255],    # Blue
        [0, 255, 0]     # Green
    ]

    brightness = 0.8  # Hardcoded brightness for this preset (0.0 to 1.0)

    # ===== SETUP STATES FOR EACH DEVICE =====
    states = {}
    for ip, count in WLED_DEVICES.items():
        states[ip] = {
            "count": count,   # Number of LEDs in this strip
            "pos_a": 0,       # Starting position of first line
            "pos_b": count - 1,# Starting position of second line
            "dir_a": 1,       # Direction of first line (1 = forward)
            "dir_b": -1       # Direction of second line (1 = forward)
        }

    global STOP_EFFECT
    while not STOP_EFFECT:
        frame_map = {}
        for ip, state in states.items():
            count = state["count"]
            leds = [[0, 0, 0] for _ in range(count)]  # Initialize frame to all off

            # ===== APPLY COLOR AND BRIGHTNESS =====
            pa_color = [int(c * brightness) for c in colors[state["pos_a"] % len(colors)]]
            pb_color = [int(c * brightness) for c in colors[state["pos_b"] % len(colors)]]

            pa, pb = int(state["pos_a"]), int(state["pos_b"])
            if 0 <= pa < count:
                leds[pa] = pa_color
            if 0 <= pb < count:
                leds[pb] = pb_color

            # ===== MOVE POSITIONS =====
            state["pos_a"] += state["dir_a"] * move_speed
            state["pos_b"] += state["dir_b"] * move_speed

            # ===== BOUNCE LOGIC =====
            if state["pos_a"] >= state["pos_b"]:
                state["dir_a"] *= -1
                state["dir_b"] *= -1
            if state["pos_a"] <= 0:
                state["dir_a"] = 1
            if state["pos_b"] >= count - 1:
                state["dir_b"] = -1

            frame_map[ip] = leds
        set_all_devices(frame_map)

        if frame_delay > 0:
            time.sleep(frame_delay)


def explosion_pulse(
    EXPLOSION_SPEED=10,
    blast_delay=0.0005,
    fade_delay=0.05
):
    """
    Explosion effect:
    - Starts at center, start, and end of LED strip
    - Expands outward quickly like an explosion
    - Randomly fades LEDs for dissipating effect
    - EXPLOSION_SPEED: how many LEDs expand per frame
    - blast_delay: delay between frames during explosion (lower = faster)
    - fade_delay: delay between frames during fade (lower = faster fade)
    - brightness: scales the intensity of the fire colors (0.0 = off, 1.0 = full)
    """
    # ===== CONFIGURABLE FIRE COLORS =====
    fire_colors = [
        [255, 0, 0],      # Pure Red
        [200, 0, 0],      # Dark Red
        [255, 69, 0],     # OrangeRed
        [255, 140, 0],    # DarkOrange
        [255, 165, 0],    # Orange
        [255, 200, 0],    # Bright Flame
        [255, 215, 0],    # Gold
    ]

    brightness = 1.0  # Hardcoded brightness for this preset

    # ===== SETUP STATES FOR EACH DEVICE =====
    states = {}
    for ip, count in WLED_DEVICES.items():
        center = count // 2
        states[ip] = {
            "count": count,
            "leds": [[0, 0, 0] for _ in range(count)],
            "center_left": center,
            "center_right": center,
            "start_pos": 0,
            "end_pos": count - 1
        }

    global STOP_EFFECT
    # ===== PHASE 1: EXPLOSION OUTWARD =====
    explosion_done = False
    while not explosion_done and not STOP_EFFECT:
        frame_map = {}
        explosion_done = True
        for ip, state in states.items():
            count = state["count"]
            leds = state["leds"]
            cl, cr = int(state["center_left"]), int(state["center_right"])
            sp, ep = int(state["start_pos"]), int(state["end_pos"])

            # Apply brightness scaling to chosen fire color
            if 0 <= cl < count:
                color = [int(c * brightness) for c in random.choice(fire_colors)]
                leds[cl] = color
            if 0 <= cr < count:
                color = [int(c * brightness) for c in random.choice(fire_colors)]
                leds[cr] = color
            if 0 <= sp < count:
                color = [int(c * brightness) for c in random.choice(fire_colors)]
                leds[sp] = color
            if 0 <= ep < count:
                color = [int(c * brightness) for c in random.choice(fire_colors)]
                leds[ep] = color

            # Move positions outward
            state["center_left"] = max(0, cl - EXPLOSION_SPEED)
            state["center_right"] = min(count - 1, cr + EXPLOSION_SPEED)
            state["start_pos"] = min(count - 1, sp + EXPLOSION_SPEED)
            state["end_pos"] = max(0, ep - EXPLOSION_SPEED)

            # Check if explosion finished
            if (state["center_left"] > 0 or state["center_right"] < count - 1
                or state["start_pos"] < count - 1 or state["end_pos"] > 0):
                explosion_done = False

            frame_map[ip] = leds
        set_all_devices(frame_map)
        time.sleep(blast_delay)

    # ===== PHASE 2: FADE OUT RANDOMLY =====
    fade_complete = False
    while not fade_complete and not STOP_EFFECT:
        frame_map = {}
        fade_complete = True
        for ip, state in states.items():
            leds = state["leds"]
            count = state["count"]
            for i in range(count):
                if leds[i] != [0, 0, 0] and random.random() < 0.1:  # 10% chance to turn off
                    leds[i] = [0, 0, 0]
            if any(led != [0, 0, 0] for led in leds):
                fade_complete = False
            frame_map[ip] = leds
        set_all_devices(frame_map)
        time.sleep(fade_delay)

# =========================================
# PRESET MAPPING
# =========================================

# Add new presets here to expand functionality
PRESETS = {
    "dual_chase_bounce": dual_chase_bounce,
    "explosion_pulse": explosion_pulse
}

# =========================================
# HELPER TO RUN PRESETS IN THREAD
# =========================================
def run_preset_thread(preset_name):
    """
    Run a preset in a separate thread.
    This allows continuous input while a preset is running.
    """
    global STOP_EFFECT
    STOP_EFFECT = False
    thread = threading.Thread(target=PRESETS[preset_name])
    thread.daemon = True
    thread.start()
    return thread

# =========================================
# RUNNER WITH CONTINUOUS COMMAND LOOP
# =========================================
if __name__ == "__main__":
    print("Available presets:")
    for name in PRESETS.keys():
        print(f" - {name}")

    current_thread = None

    while True:
        selected = input("\nEnter preset name to run (or 'exit' to quit): ").strip()
        if selected.lower() == "exit":
            STOP_EFFECT = True
            print("Exiting program.")
            break
        if selected in PRESETS:
            # Stop previous effect
            STOP_EFFECT = True
            time.sleep(0.05)  # allow previous thread to stop
            # Start new preset
            current_thread = run_preset_thread(selected)
            print(f"Running preset: {selected}")
        else:
            print(f"Preset '{selected}' not found.")
