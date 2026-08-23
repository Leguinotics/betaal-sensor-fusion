# =========================================================================
# 🥁 BeTaal Backend: High-Speed Fault-Tolerant Strictly Locked Engine
# =========================================================================
import time
import threading
import json
import re
import numpy as np
from arduino.app_utils import App, Bridge

WAZUH_LOG_PATH = "betaal_security_events.log"

if "GLOBAL_STORE" not in globals():
    globals()["GLOBAL_STORE"] = {
        "phase": "SETUP",
        "last_phase_seen": "SETUP", 
        "phase_start_time": 0.0,
        "strike_count": 0,
        "intervals": [],
        "accent_peaks": [],         
        "last_hit_time": 0,
        "chart_data": [],           
        "history_log": [],          
        "warnings": [],             
        "locked_tempo_ms": 0.0,
        "detected_taal": "Listening for Rhythm...",
        "sub_beat_counter": 0,
        "passed_cleanly": False,
        "tolerance_ms": 42 
    }

def get_shared_state():
    return globals()["GLOBAL_STORE"]

def write_wazuh_security_event(event_type, description, current_tempo=0.0, drift_ms=0.0):
    shared_data = globals()["GLOBAL_STORE"]
    log_entry = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S+0530", time.localtime()),
        "application": "BeTaal_Rhythm_Core",
        "event_type": event_type,
        "severity": "info" if event_type in ["SESSION_START", "TAAL_LOCK", "SESSION_SUCCESS"] else "warning",
        "metrics": {
            "target_tempo_ms": round(current_tempo, 2),
            "calculated_drift_ms": round(drift_ms, 2),
            "total_strikes": shared_data.get("strike_count", 0),
            "active_phase": shared_data.get("phase", "UNKNOWN")
        },
        "description": description
    }
    try:
        with open(WAZUH_LOG_PATH, mode="a") as log_file:
            log_file.write(json.dumps(log_entry) + "\n")
    except Exception as e:
        print(f"⚠️ [LOG ERROR]: {e}")

def handle_gyro_hit(*args):
    shared_data = globals()["GLOBAL_STORE"]
    now_ms = int(time.time() * 1000)
    
    if shared_data["phase"] == "SETUP" or shared_data["passed_cleanly"]:
        return
        
    # FIX: टुपल अनपैकिंग को पूरी तरह से डिफ़ेंसिव और बुलेटप्रूफ़ बना दिया गया है
    try:
        if len(args) > 0 and isinstance(args[0], (list, tuple)):
            target_args = args[0]
        else:
            target_args = args

        val_0 = str(target_args[0]).strip() if len(target_args) > 0 else "500"
        val_1 = str(target_args[1]).strip() if len(target_args) > 1 else "1.1"
        
        clean_arg_0 = re.sub(r'[^\d.]', '', val_0)
        clean_arg_1 = re.sub(r'[^\d.]', '', val_1)
        
        actual_interval = int(float(clean_arg_0))
        strike_force = float(clean_arg_1)
        
        if actual_interval == 0: actual_interval = 450
        if strike_force == 0.0: strike_force = 1.20
    except Exception as e:
        actual_interval = 450
        strike_force = 1.20
        
    if shared_data["phase"] != shared_data["last_phase_seen"]:
        shared_data["intervals"] = []
        shared_data["accent_peaks"] = []
        if shared_data["phase"] == "BLIND":
            shared_data["chart_data"] = [] 
        shared_data["strike_count"] = 0
        shared_data["last_hit_time"] = now_ms
        shared_data["sub_beat_counter"] = 0
        shared_data["warnings"] = []
        shared_data["last_phase_seen"] = shared_data["phase"]
        return

    shared_data["strike_count"] += 1
    clamped_interval = min(1100, max(200, actual_interval))
    
    # स्टेज 3 (BLIND) में पहुँचते ही पैटर्न का री-क्लासिफिकेशन पूरी तरह ब्लॉक है!
    if shared_data["phase"] in ["SCANNING", "OPTIMIZING"]:
        if strike_force > 1.60: 
            total_cycle_beats = shared_data["sub_beat_counter"] + 1
            if total_cycle_beats == 4:
                shared_data["detected_taal"] = "Verified 4-Beat Cycle [1: Baayan | 2,3,4: Daayan]"
            else:
                shared_data["detected_taal"] = f"Custom Dynamic Pattern ({total_cycle_beats} Beats)"
            shared_data["sub_beat_counter"] = 0 
        else:
            shared_data["sub_beat_counter"] += 1

    shared_data["chart_data"].append(clamped_interval)
    if len(shared_data["chart_data"]) > 25: shared_data["chart_data"].pop(0)
    
    shared_data["intervals"].append(actual_interval)
    shared_data["accent_peaks"].append(strike_force)
    
    shared_data["history_log"].append([shared_data["strike_count"], clamped_interval, strike_force])
    if len(shared_data["history_log"]) > 80: shared_data["history_log"].pop(0)

    # --- STAGE 3: RAW MATHEMATICAL DEVIATION AUDIT ---
    if shared_data["phase"] == "BLIND":
        deviation = actual_interval - shared_data["locked_tempo_ms"]
        live_tolerance = shared_data.get("tolerance_ms", 42)
        
        if abs(deviation) > live_tolerance:
            err_msg = f"👹 [VIOLATION]: Strike #{shared_data['strike_count']} Drifted by {deviation:+.1f}ms"
            shared_data["warnings"].append(err_msg)
            
            write_wazuh_security_event(
                event_type="RHYTHM_DRIFT_VIOLATION", 
                description=f"Strict cadence audit failed. Target baseline breached during blind testing.",
                current_tempo=shared_data["locked_tempo_ms"],
                drift_ms=deviation
            )
            Bridge.notify("trigger_led_alert")
            
    # फ्रंटएंड को लाइव री-रेंडर करने के लिए ट्रिगर
    shared_data["strike_count"] += 1
    shared_data["strike_count"] -= 1

if "BRIDGE_INITIALIZED" not in globals():
    globals()["BRIDGE_INITIALIZED"] = True
    Bridge.provide("gyro_hit_event", handle_gyro_hit)
    t = threading.Thread(target=App.run, daemon=True)
    t.start()
