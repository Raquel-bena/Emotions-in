# server.py - EL CEREBRO
import time
import threading
import requests
import random
import math
from flask import Flask, render_template
from flask_socketio import SocketIO, emit

# --- CONFIGURACIÓN ---
PORT = 3000
HOST_IP = '0.0.0.0' # Permite conexiones externas

# TUS CLAVES REALES
KEYS = {
    'OWM': '09a95abe51374eae766a284a97a3f039',
    'TMB_ID': 'daf62db0',
    'TMB_KEY': '5e4adb21bdfeda65a91e36cc2c12b7df'
}

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# --- ESTADO GLOBAL ---
system_state = {
    'weather': {'temp': 15, 'humidity': 50, 'wind': 0},
    'transit': {'congestion': 0.5, 'active_trains': 10},
    'noise': {'db': 40}
}

# --- HILO 1: DATOS REALES (Cada 60s) ---
def fetch_apis():
    while True:
        try:
            # CLIMA
            w_url = f"http://api.openweathermap.org/data/2.5/weather?q=Barcelona,ES&appid={KEYS['OWM']}&units=metric"
            r_w = requests.get(w_url).json()
            if r_w.get('main'):
                system_state['weather']['temp'] = r_w['main']['temp']
                system_state['weather']['humidity'] = r_w['main']['humidity']
                system_state['weather']['wind'] = r_w['wind']['speed']
                print(f"Update Clima: {system_state['weather']['temp']}°C")

            # METRO
            t_url = f"https://api.tmb.cat/v1/transit/linies/metro?app_id={KEYS['TMB_ID']}&app_key={KEYS['TMB_KEY']}"
            r_t = requests.get(t_url).json()
            if r_t.get('features'):
                total_lines = len(r_t['features'])
                # Simulación de congestión basada en hora real
                current_hour = time.localtime().tm_hour
                is_rush_hour = (8 <= current_hour <= 10) or (18 <= current_hour <= 20)
                system_state['transit']['congestion'] = 0.9 if is_rush_hour else 0.4
                print(f"Update Metro: {total_lines} lineas activas")

        except Exception as e:
            print(f"Error API: {e}")
        
        time.sleep(60)

# --- HILO 2: LATIDO VISUAL (Cada 0.05s) ---
def pulse_generator():
    while True:
        t = time.time()
        fast_data = {
            'w_temp': system_state['weather']['temp'],
            'w_wave': math.sin(t * 0.5 + system_state['weather']['wind']),
            't_congestion': system_state['transit']['congestion'],
            't_pulse': (math.sin(t * 5) + 1) / 2 if system_state['transit']['congestion'] > 0.7 else (math.sin(t) + 1) / 2,
            'n_db': random.uniform(30, 90),
            'timestamp': t
        }
        socketio.emit('data_pulse', fast_data)
        time.sleep(0.05)

@app.route('/')
def index():
    return "SERVER ONLINE. Conecta las pantallas."

@app.route('/screen<int:id>')
def screen(id):
    return render_template('visualizer.html', screen_id=id)

if __name__ == '__main__':
    threading.Thread(target=fetch_apis, daemon=True).start()
    threading.Thread(target=pulse_generator, daemon=True).start()
    print(f"--- SISTEMA LISTO EN: http://192.168.1.38:{PORT} ---")
    socketio.run(app, host=HOST_IP, port=PORT)