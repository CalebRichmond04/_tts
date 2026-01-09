import time
import random
import requests
import threading

# ================= DEVICE CONFIG =================
WLED_DEVICES = {
    "192.168.1.124": 209,
    "192.168.1.69": 174
}

STOP_EFFECT = False
current_thread = None

# ===============================================
# ====== HELPER FUNCTIONS FOR LED CONTROL ======
# ===============================================

def set_leds(ip, leds):
    payload = {"on": True, "seg": {"i": leds}}
    try:
        requests.post(f"http://{ip}/json/state", json=payload, timeout=0.3)
    except:
        pass

def set_all_devices(frame_map):
    for ip, leds in frame_map.items():
        set_leds(ip, leds)

# =========================================
# ====== PRESETS / EFFECT FUNCTIONS =======
# =========================================

def dual_chase_bounce(move_speed=10, frame_delay=0):
    colors = [
        [255, 215, 0],
        [255, 255, 255],
        [0, 0, 255],
        [0, 255, 0]
    ]

    brightness = 0.8

    states = {}
    for ip, count in WLED_DEVICES.items():
        states[ip] = {
            "count": count,
            "pos_a": 0,
            "pos_b": count - 1,
            "dir_a": 1,
            "dir_b": -1
        }

    global STOP_EFFECT
    while not STOP_EFFECT:
        frame_map = {}
        for ip, state in states.items():
            count = state["count"]
            leds = [[0, 0, 0] for _ in range(count)]

            pa_color = [int(c * brightness) for c in colors[state["pos_a"] % len(colors)]]
            pb_color = [int(c * brightness) for c in colors[state["pos_b"] % len(colors)]]

            pa, pb = int(state["pos_a"]), int(state["pos_b"])
            if 0 <= pa < count:
                leds[pa] = pa_color
            if 0 <= pb < count:
                leds[pb] = pb_color

            state["pos_a"] += state["dir_a"] * move_speed
            state["pos_b"] += state["dir_b"] * move_speed

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


def explosion_pulse(EXPLOSION_SPEED=10, blast_delay=0.0005, fade_delay=0.05):
    fire_colors = [
        [255, 0, 0],
        [200, 0, 0],
        [255, 69, 0],
        [255, 140, 0],
        [255, 165, 0],
        [255, 200, 0],
        [255, 215, 0],
    ]

    brightness = 1.0

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

    explosion_done = False
    while not explosion_done and not STOP_EFFECT:
        frame_map = {}
        explosion_done = True
        for ip, state in states.items():
            count = state["count"]
            leds = state["leds"]
            cl, cr = int(state["center_left"]), int(state["center_right"])
            sp, ep = int(state["start_pos"]), int(state["end_pos"])

            if 0 <= cl < count:
                leds[cl] = [int(c * brightness) for c in random.choice(fire_colors)]
            if 0 <= cr < count:
                leds[cr] = [int(c * brightness) for c in random.choice(fire_colors)]
            if 0 <= sp < count:
                leds[sp] = [int(c * brightness) for c in random.choice(fire_colors)]
            if 0 <= ep < count:
                leds[ep] = [int(c * brightness) for c in random.choice(fire_colors)]

            state["center_left"] = max(0, cl - EXPLOSION_SPEED)
            state["center_right"] = min(count - 1, cr + EXPLOSION_SPEED)
            state["start_pos"] = min(count - 1, sp + EXPLOSION_SPEED)
            state["end_pos"] = max(0, ep - EXPLOSION_SPEED)

            if (state["center_left"] > 0 or state["center_right"] < count - 1
                or state["start_pos"] < count - 1 or state["end_pos"] > 0):
                explosion_done = False

            frame_map[ip] = leds

        set_all_devices(frame_map)
        time.sleep(blast_delay)

    fade_complete = False
    while not fade_complete and not STOP_EFFECT:
        frame_map = {}
        fade_complete = True
        for ip, state in states.items():
            leds = state["leds"]
            count = state["count"]
            for i in range(count):
                if leds[i] != [0, 0, 0] and random.random() < 0.1:
                    leds[i] = [0, 0, 0]
            if any(led != [0, 0, 0] for led in leds):
                fade_complete = False
            frame_map[ip] = leds

        set_all_devices(frame_map)
        time.sleep(fade_delay)

# =========================================
# PRESET MAPPING
# =========================================

PRESETS = {
    "dual_chase_bounce": dual_chase_bounce,
    "explosion_pulse": explosion_pulse
}

# =========================================
# CONTROL FUNCTIONS (CALLED BY MAIN.PY)
# =========================================

def start_preset(preset_name):
    global STOP_EFFECT, current_thread

    if preset_name not in PRESETS:
        print(f"Preset '{preset_name}' not found.")
        return

    stop_preset()

    STOP_EFFECT = False
    current_thread = threading.Thread(target=PRESETS[preset_name])
    current_thread.daemon = True
    current_thread.start()

def stop_preset():
    global STOP_EFFECT
    STOP_EFFECT = True
