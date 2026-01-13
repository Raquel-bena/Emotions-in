#!/usr/bin/env python3
"""
Publisher MQTT robusto para Raspberry Pi Zero 2 WH
"""
import json
import time
import requests
import paho.mqtt.client as mqtt
from datetime import datetime
import threading
import random
from api_keys import *

class EmotionsPublisher:
    def __init__(self):
        self.client = mqtt.Client(client_id="emotions_publisher")
        # Solo configurar usuario si se ha definido contraseña
        if MQTT_PASSWORD and MQTT_PASSWORD != "secure_password_here":
            self.client.username_pw_set(MQTT_USER, MQTT_PASSWORD)
            
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        
        self.current_weather = None
        self.current_tmb = None
        self.current_pulse = 75

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print(f"✅ [MQTT] Conectado al broker en {MQTT_BROKER}")
        else:
            print(f"❌ [MQTT] Error de conexión: {rc}")

    def on_disconnect(self, client, userdata, rc):
        print("⚠️ [MQTT] Desconectado. Intentando reconectar...")

    def get_weather_data(self, city="Barcelona"):
        """Obtiene datos reales de OpenWeatherMap"""
        try:
            params = {
                'q': city,
                'appid': WEATHER_API_KEY,
                'units': 'metric',
                'lang': 'es'
            }
            response = requests.get(OPENWEATHER_URL, params=params, timeout=10)
            
            if response.status_code == 401: 
                raise ValueError("API Key inválida")
                
            response.raise_for_status()
            data = response.json()
            
            weather_data = {
                'city': data['name'],
                'temp': round(data['main']['temp'], 1),
                'humidity': data['main']['humidity'],
                'wind_speed': round(data['wind']['speed'] * 3.6, 1),
                'condition': data['weather'][0]['main'],
                'description': data['weather'][0]['description'].capitalize(),
                'timestamp': datetime.now().isoformat()
            }
            weather_data['emotion'] = self.determine_weather_emotion(weather_data)
            self.current_weather = weather_data
            return weather_data
            
        except Exception as e:
            print(f"⚠️ [Clima] Fallo API ({e}). Usando datos simulados.")
            return self.current_weather or {
                'city': city,
                'temp': 24.5,
                'condition': 'Clear',
                'description': 'Simulado (Sin conexión)',
                'humidity': 50,
                'wind_speed': 10,
                'emotion': 'happy',
                'timestamp': datetime.now().isoformat()
            }

    def determine_weather_emotion(self, weather_data):
        temp = weather_data['temp']
        condition = weather_data['condition']
        for emotion, thresholds in WEATHER_EMOTION_THRESHOLDS.items():
            if thresholds['temp_min'] <= temp <= thresholds['temp_max'] and condition in thresholds['conditions']:
                return emotion
        return 'neutral'

    def get_tmb_data(self):
        """Intenta obtener datos reales de TMB (iBus), si falla, simula"""
        try:
            # URL real de la API de TMB para iBus
            url = f"https://api.tmb.cat/v1/ibus/stops/{TMB_STOP_ID}?app_id={TMB_APP_ID}&app_key={TMB_APP_KEY}"
            
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                next_buses = []
                
                if 'data' in data and 'ibus' in data['data']:
                    for bus in data['data']['ibus']:
                        next_buses.append({
                            'line': bus['line'],
                            'minutes': bus['t-in-min']
                        })
                
                next_buses = sorted(next_buses, key=lambda x: x['minutes'])
                
                tmb_data = {
                    'stop_id': TMB_STOP_ID,
                    'stop_name': 'Parada TMB Real',
                    'next_buses': next_buses[:3],
                    'timestamp': datetime.now().isoformat()
                }
                
                is_rushing = any(b['minutes'] < 2 for b in next_buses)
                tmb_data['emotion'] = 'energetic' if is_rushing else 'calm'
                
                self.current_tmb = tmb_data
                return tmb_data
            else:
                raise Exception(f"Status {response.status_code}")

        except Exception as e:
            # Fallback a simulación
            next_buses = [
                {'line': 'V13', 'minutes': random.randint(1, 15)},
                {'line': 'H16', 'minutes': random.randint(2, 20)},
                {'line': '59',  'minutes': random.randint(5, 25)}
            ]
            next_buses = sorted(next_buses, key=lambda x: x['minutes'])
            
            return {
                'stop_name': 'Parada Simulada',
                'next_buses': next_buses,
                'emotion': 'energetic' if next_buses[0]['minutes'] < 5 else 'calm',
                'timestamp': datetime.now().isoformat()
            }

    def simulate_pulse_data(self):
        base_pulse = 72
        variation = random.uniform(-5, 5)
        self.current_pulse = int(base_pulse + variation)
        return {
            'bpm': self.current_pulse,
            'quality': 'good',
            'timestamp': datetime.now().isoformat(),
            'emotion': 'anxious' if self.current_pulse > 90 else 'calm'
        }

    # --- BUCLES DE PUBLICACIÓN ---
    def publish_loop(self, topic, data_func, interval, label):
        while True:
            data = data_func()
            if data:
                try:
                    self.client.publish(topic, json.dumps(data), qos=1)
                    print(f"📤 [{label}] Enviado: {data.get('emotion', 'N/A')}")
                except Exception as e:
                    print(f"❌ Error publicando {label}: {e}")
            time.sleep(interval)

    def start(self):
        print("🚀 Iniciando Emotions Publisher (Multi-Thread)...")
        try:
            self.client.connect(MQTT_BROKER, MQTT_PORT, 60)
            self.client.loop_start()

            # Hilos independientes
            threading.Thread(target=self.publish_loop, args=(CLIMA_TOPIC, self.get_weather_data, 300, "Clima"), daemon=True).start()
            threading.Thread(target=self.publish_loop, args=(TMB_TOPIC, self.get_tmb_data, 60, "TMB"), daemon=True).start()
            threading.Thread(target=self.publish_loop, args=(PULSE_TOPIC, self.simulate_pulse_data, 2, "Pulso"), daemon=True).start()

            while True: time.sleep(1) # Mantener vivo
            
        except KeyboardInterrupt:
            print("\n🛑 Deteniendo...")
            self.client.loop_stop()

if __name__ == "__main__":
    EmotionsPublisher().start()
    