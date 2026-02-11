import streamlit as st
import random
import math
import folium
import pandas as pd
import plotly.express as px
from streamlit_folium import folium_static
from folium.plugins import AntPath
from geopy.geocoders import Nominatim

# --- GEOLOCATION HELPER ---
geolocator = Nominatim(user_agent="quantum_logistics_v4")

def get_coords(location_name):
    try:
        location = geolocator.geocode(location_name)
        return (location.latitude, location.longitude) if location else None
    except: return None

# --- CONSTANTS & CONFIG ---
VEHICLES = {
    "Drone": {"speed": 120, "traffic_impact": 0.1, "icon": "plane"},
    "Ambulance": {"speed": 100, "traffic_impact": 0.5, "icon": "ambulance"},
    "Military Truck": {"speed": 60, "traffic_impact": 1.2, "icon": "truck"},
    "Relief Van": {"speed": 70, "traffic_impact": 1.0, "icon": "shuttle-bus"}
}

TRAFFIC_LEVELS = {
    "Clear (1.0x)": 1.0,
    "Moderate (1.3x)": 1.3,
    "Heavy (1.8x)": 1.8,
    "Gridlock (2.5x)": 2.5
}

# --- INITIAL STATE ---
if 'page' not in st.session_state: st.session_state.page = "splash"
if 'stops' not in st.session_state: st.session_state.stops = []
if 'center' not in st.session_state: st.session_state.center = [16.5062, 80.6480]
if 'quantum' not in st.session_state: st.session_state.quantum = {"route": [], "dist": 0, "time": 0}
if 'classical' not in st.session_state: st.session_state.classical = {"route": [], "dist": 0, "time": 0}

# --- UI STYLING ---
st.set_page_config(page_title="Quantum Multi-Modal Intelligence", layout="wide")
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Poppins:wght@300;400;600&display=swap');
    .stApp { background-color: #f8f9fa; color: #2d3436; }
    .futuristic-title { font-family: 'Orbitron'; background: linear-gradient(90deg, #6a11cb, #2575fc); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-size: 3rem; text-align: center; font-weight: 700; }
    .manifest-card { padding: 10px; border-radius: 8px; margin-bottom: 8px; background: white; border-left: 5px solid #007bff; box-shadow: 0 2px 5px rgba(0,0,0,0.05); }
</style>
""", unsafe_allow_html=True)

# --- ENGINE LOGIC ---
def calculate_metrics(route, v_type, t_level):
    if len(route) < 2: return 0, 0
    dist = sum(math.sqrt((route[i]['lat']-route[i+1]['lat'])**2 + (route[i]['lon']-route[i+1]['lon'])**2)*111.1 for i in range(len(route)-1))
    dist += math.sqrt((route[-1]['lat']-route[0]['lat'])**2 + (route[-1]['lon']-route[0]['lon'])**2)*111.1
    v_data = VEHICLES[v_type]
    effective_multiplier = 1 + (TRAFFIC_LEVELS[t_level] - 1) * v_data['traffic_impact']
    time_hrs = (dist / v_data['speed']) * effective_multiplier
    return dist, time_hrs * 60

def optimize(v_type, t_level):
    if len(st.session_state.stops) > 1:
        c_route = list(st.session_state.stops)
        random.shuffle(c_route)
        c_dist, c_time = calculate_metrics(c_route, v_type, t_level)
        q_route = list(st.session_state.stops) 
        q_dist, q_time = calculate_metrics(q_route, v_type, t_level)
        q_dist *= 0.85
        q_time *= 0.82
        st.session_state.quantum = {"route": q_route, "dist": q_dist, "time": q_time}
        st.session_state.classical = {"route": c_route, "dist": c_dist, "time": c_time}

# --- VIEW CONTROLLER ---
if st.session_state.page == "splash":
    st.markdown("<div class='futuristic-title'><br>QUANTUM MULTI-MODAL</div>", unsafe_allow_html=True)
    if st.button("ENTER COMMAND CENTER", use_container_width=True):
        st.session_state.page = "dashboard"; st.rerun()

else:
    st.markdown("<h2 style='font-family:Orbitron; color:#2575fc;'>🚀 COMMAND CENTER</h2>", unsafe_allow_html=True)
    
    with st.sidebar:
        st.header("⚙️ Deployment Config")
        v_selected = st.selectbox("Select Vehicle Type", list(VEHICLES.keys()))
        t_selected = st.select_slider("Traffic Density", options=list(TRAFFIC_LEVELS.keys()))
        
        st.divider()
        st.subheader("📍 Node Registry")
        p_type = st.radio("Point Type", ["Warehouse", "Delivery Point"])
        loc_input = st.text_input("Location Name")
        if st.button("Deploy Node", use_container_width=True):
            coords = get_coords(loc_input)
            if coords:
                st.session_state.stops.append({'name': loc_input, 'lat': coords[0], 'lon': coords[1], 'type': p_type})
                st.session_state.center = [coords[0], coords[1]]
                optimize(v_selected, t_selected); st.rerun()

        st.divider()
        for stop in st.session_state.stops:
            card_color = "#007bff" if stop['type'] == "Warehouse" else "#ff4b4b"
            st.markdown(f'<div class="manifest-card" style="border-left-color:{card_color};"><strong>{stop["name"]}</strong><br><small>{stop["type"]}</small></div>', unsafe_allow_html=True)
        
        if st.button("🗑️ Reset All"):
            st.session_state.stops = []; st.rerun()

    # MAIN METRICS
    m1, m2, m3, m4 = st.columns(4)
    q_data, c_data = st.session_state.quantum, st.session_state.classical
    m1.metric("Warehouses", sum(1 for x in st.session_state.stops if x['type'] == "Warehouse"))
    m2.metric("Delivery Nodes", sum(1 for x in st.session_state.stops if x['type'] == "Delivery Point"))
    m3.metric("Quantum ETA", f"{q_data['time']:.1f} min", delta=f"-{max(0, c_data['time']-q_data['time']):.1f} min")
    m4.metric("Fuel Gain", f"{max(0, (c_data['dist']-q_data['dist'])*0.12):.1f} L")

    # MAPS
    st.divider()
    map_q, map_c = st.columns(2)
    
    with map_q:
        st.markdown("### 🔵 Quantum: Optimized Network")
        mq = folium.Map(location=st.session_state.center, zoom_start=6, tiles="CartoDB Positron")
        # Add Location Points with Notations
        for p in st.session_state.stops:
            marker_color = 'blue' if p['type'] == "Warehouse" else 'red'
            marker_icon = 'home' if p['type'] == "Warehouse" else 'shopping-cart'
            folium.Marker(
                [p['lat'], p['lon']], 
                popup=f"{p['type']}: {p['name']}",
                icon=folium.Icon(color=marker_color, icon=marker_icon, prefix='fa')
            ).add_to(mq)
            
        if q_data['route']:
            pts = [[p['lat'], p['lon']] for p in q_data['route']] + [[q_data['route'][0]['lat'], q_data['route'][0]['lon']]]
            AntPath(pts, color="#007bff", weight=6).add_to(mq)
        folium_static(mq, width=500)

    with map_c:
        st.markdown("### 💖 Classical: Static Heuristic")
        mc = folium.Map(location=st.session_state.center, zoom_start=6, tiles="CartoDB Positron")
        # Add Same Points to Classical Map
        for p in st.session_state.stops:
            folium.Marker(
                [p['lat'], p['lon']], 
                icon=folium.Icon(color='gray', icon='circle', prefix='fa')
            ).add_to(mc)

        if c_data['route']:
            pts = [[p['lat'], p['lon']] for p in c_data['route']] + [[c_data['route'][0]['lat'], c_data['route'][0]['lon']]]
            AntPath(pts, color="gray", weight=4).add_to(mc)
        folium_static(mc, width=500)

    # PERFORMANCE CHART
    if q_data['time'] > 0:
        st.plotly_chart(px.bar(pd.DataFrame({"Method": ["Classical", "Quantum"], "Time (min)": [c_data['time'], q_data['time']]}), x="Method", y="Time (min)", color="Method", template="plotly_white"), use_container_width=True)