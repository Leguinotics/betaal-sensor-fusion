import time
import json
import random
import logging
import numpy as np
import streamlit as st
import pandas as pd

st.set_page_config(page_title="BeTaal AI Arena", page_icon="🥁", layout="wide")
WAZUH_LOG_PATH = "betaal_security_events.log"

logger = logging.getLogger("BeTaalSIEM")
logger.setLevel(logging.INFO)
if not logger.handlers:
    try:
        file_handler = logging.FileHandler(WAZUH_LOG_PATH, mode="a", encoding="utf-8")
        formatter = logging.Formatter('%(message)s')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except Exception:
        pass

for key, default_value in {
    "phase": "SETUP",
    "phase_start_time": 0.0,
    "gaps_records_pool": [],
    "force_records_pool": [],
    "strike_indexer": 0,
    "locked_tempo_ms": 450.0,
    "detected_taal": "Verified 4-Beat Repetitions Locked",
    "warnings_count": 0,
    "tolerance_ms": 42,
    "loop_complete_triggered": False
}.items():
    if key not in st.session_state:
        st.session_state[key] = default_value

def write_wazuh_security_event(event_type, desc, severity="info"):
    log_entry = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S+0530", time.localtime()),
        "application": "BeTaal_Rhythm_Core",
        "severity": severity,
        "event_type": event_type,
        "description": desc,
        "data": {
            "event_type": event_type,
            "active_phase": str(st.session_state["phase"]),
            "total_strikes": int(st.session_state["strike_indexer"]),
            "target_tempo_ms": float(st.session_state["locked_tempo_ms"])
        }
    }
    try:
        logger.info(json.dumps(log_entry))
    except Exception:
        pass

st.markdown("<style>.vikram-epic{background:linear-gradient(135deg,#e6c619 0%,#b8860b 100%);padding:25px;border-radius:12px;text-align:center;box-shadow:0px 4px 15px rgba(230,198,25,0.4);border:2px solid #ffd700;}.betaal-gothic{background:linear-gradient(135deg,#4a0e17 0%,#1a0508 100%);padding:25px;border-radius:12px;text-align:center;box-shadow:0px 4px 15px rgba(255,0,0,0.3);border:2px solid #8b0000;}</style>", unsafe_allow_html=True)

st.title("BeTaal: Tabla Sensor-Fusion Arena")

if st.session_state["phase"] != "SETUP":
    if st.button("Reset Project Arena Loop", type="secondary", use_container_width=True):
        st.session_state["phase"] = "SETUP"
        st.session_state["gaps_records_pool"] = []
        st.session_state["force_records_pool"] = []
        st.session_state["strike_indexer"] = 0
        st.session_state["warnings_count"] = 0
        st.session_state["loop_complete_triggered"] = False
        st.session_state["detected_taal"] = "Verified 4-Beat Repetitions Locked"
        st.rerun()

if st.session_state["phase"] == "SETUP":
    st.subheader("Betaal Challenge: Strict Mode Tracker")
    st.session_state["tolerance_ms"] = st.slider("Allowed Drift Window (Strict Mode Tolerance +/- ms)", 20, 100, 42)
    
    if st.button("Initialize Strict Rhythm Audit Run", type="primary", use_container_width=True):
        st.session_state["phase"] = "SCANNING"
        st.session_state["phase_start_time"] = time.time()
        st.session_state["gaps_records_pool"] = []
        st.session_state["force_records_pool"] = []
        st.session_state["strike_indexer"] = 0
        st.session_state["warnings_count"] = 0
        st.session_state["loop_complete_triggered"] = False
        st.session_state["detected_taal"] = "Verified 4-Beat Repetitions Locked"
        write_wazuh_security_event("SESSION_START", "Activated.")
        st.rerun()
else:
    if st.session_state["warnings_count"] > 0:
        st.error(f"🚨 STATUS MATRIX: {st.session_state['detected_taal']} [Violations: {st.session_state['warnings_count']}]")
    else:
        st.success(f"✨ STATUS MATRIX: {st.session_state['detected_taal']}")
        
    m1, m2 = st.columns(2)
    with m1: 
        st.metric("AI Tempo Target Baseline", f"{st.session_state['locked_tempo_ms']:.1f} ms")
        st.caption(f"🎯 Boundary Drift Window Limit: **+/- {st.session_state['tolerance_ms']} ms**")
    with m2:
        elapsed = time.time() - st.session_state["phase_start_time"]
        if elapsed <= 60.0:
            if elapsed <= 30.0: st.info(f"⏱️ Stage 1 (Observe Taps): {max(0, int(30.0 - elapsed))}s left")
            elif elapsed <= 45.0: st.warning(f"🧠 Stage 2 (Optimize Baseline): {max(0, int(45.0 - elapsed))}s left")
            elif elapsed <= 60.0: st.error(f"🔒 Stage 3 (Strict AI Test): {max(0, round(60.0 - elapsed))}s left")

    st.markdown("---")
    
    if elapsed <= 60.0:
        st.session_state["strike_indexer"] += 1
        
        if elapsed <= 45.0:
            drift = random.randint(-6, 6)
        else:
            drift = random.randint(-55, 55)
            
        calculated_gap = int(st.session_state["locked_tempo_ms"] + drift)
        calculated_force = round(float(random.uniform(1.20, 2.10)), 2)

        st.session_state["gaps_records_pool"].append({"Strike": int(st.session_state["strike_indexer"]), "Interval": int(calculated_gap)})
        st.session_state["force_records_pool"].append({"Strike": int(st.session_state["strike_indexer"]), "Force": float(calculated_force)})

        if len(st.session_state["gaps_records_pool"]) > 35:
            st.session_state["gaps_records_pool"].pop(0)
            st.session_state["force_records_pool"].pop(0)

        if elapsed <= 30.0:
            st.session_state["detected_taal"] = "Verified 4-Beat Repetitions Locked"
        elif elapsed <= 45.0:
            if st.session_state["phase"] != "OPTIMIZING": st.session_state["phase"] = "OPTIMIZING"
            gaps_only = [item["Interval"] for item in st.session_state["gaps_records_pool"]]
            if gaps_only: st.session_state["locked_tempo_ms"] = float(np.mean(gaps_only))
            st.session_state["detected_taal"] = "🧠 Target Baseline Optimized & Template Locked!"
        else:
            if st.session_state["phase"] != "TESTING": st.session_state["phase"] = "TESTING"
            deviation = abs(calculated_gap - st.session_state["locked_tempo_ms"])
            if deviation > st.session_state["tolerance_ms"]:
                st.session_state["detected_taal"] = f"🚨 BETAAL DETECTED (FAIL) - Tempo Cadence Split by {deviation:.0f}ms!"
                st.session_state["warnings_count"] += 1
                write_wazuh_security_event("RHYTHM_DRIFT_VIOLATION", f"Drift limit broken by {deviation}ms", "warning")
            else:
                st.session_state["detected_taal"] = "⚔️ RHYTHM PERFECT (PASS) - Maintaining Cadence"
    else:
        if not st.session_state["loop_complete_triggered"]:
            st.session_state["loop_complete_triggered"] = True
            write_wazuh_security_event("CHALLENGE_COMPLETE", f"Finished with total violations: {st.session_state['warnings_count']}")
            st.rerun()

        if st.session_state["warnings_count"] == 0 and len(st.session_state["gaps_records_pool"]) > 0:
            st.balloons()
            st.markdown('<div class="vikram-epic"><h1 style="color:#ffffff;margin:0;font-size:2.3rem;text-shadow:2px 2px 4px #000000;">⚔️ VEER VIKRAM KI AKHAND VIJAY! ⚔️</h1><p style="color:#fdf5e6;font-size:1.2rem;margin-top:10px;font-weight:bold;">INTENSE VICTORY! Flawless Local Cadence Evaluation Active!</p></div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="betaal-gothic"><h1 style="color:#ff4d4d;margin:0;font-size:2.3rem;text-shadow:2px 2px 4px #000000;">👹 HA HA HA! BETAAL KHUSH HUA! 👹</h1><p style="color:#ffcccc;font-size:1.2rem;margin-top:10px;font-weight:bold;">Vikram ka niyam tootna! Lay khandit hui! Fail Verified!<br>[Total Faults Ingested: ' + str(st.session_state["warnings_count"]) + ']</p></div>', unsafe_allow_html=True)

    gaps_arr = list(st.session_state["gaps_records_pool"])
    force_arr = list(st.session_state["force_records_pool"])
    
    if gaps_arr and force_arr:
        try:
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("##### Sensor 1: Cadence Wavelength Gaps (ms)")
                df_gaps = pd.DataFrame(gaps_arr).set_index("Strike")
                st.line_chart(df_gaps, height=220, use_container_width=True)
            with col2:
                st.markdown("##### Sensor 2: Impact Force Amplitude (g)")
                df_force = pd.DataFrame(force_arr).set_index("Strike")
                st.line_chart(df_force, height=220, use_container_width=True)
        except Exception:
            pass

    if not st.session_state["loop_complete_triggered"]:
        time.sleep(0.35)
        st.rerun()
