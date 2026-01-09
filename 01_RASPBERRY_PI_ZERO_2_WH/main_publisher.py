#!/usr/bin/env python3
"""
Publisher MQTT para datos de clima, transporte y pulso
Ejecutar como servicio en Raspberry Pi Zero 2 WH
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
        self.client.username_pw_set(MQTT_USER, MQTT_PASSWORD)
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        
        # Estado actual
        self.current_weather = None
        self.current_tmb = None
        self.current_pulse = 75  # Valor inicial simulado
        
    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print("✅ Conectado al broker MQTT")
        else:
            print(f"❌ Error de conexión MQTT: {rc}")
            
    def on_disconnect(self, client, userdata, rc):
        print("🔌 Desconectado del broker MQTT")
        self.reconnect()
    
    def reconnect(self):
        while True:
            try:
                print("🔄 Intentando reconectar al broker MQTT...")
                self.client.reconnect()
                break
            except:
                time.sleep(5)
    
    def get_weather_data(self, city="Barcelona"):
        """Obtiene datos del clima desde OpenWeatherMap"""
        try:
            params = {
                'q': city,
                'appid': WEATHER_API_KEY,
                'units': 'metric',
                'lang': 'es'
            }
            response = requests.get(OPENWEATHER_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Procesar datos relevantes
            weather_data = {
                'city': data['name'],
                'temp': round(data['main']['temp'], 1),
                'feels_like': round(data['main']['feels_like'], 1),
                'humidity': data['main']['humidity'],
                'pressure': data['main']['pressure'],
                'wind_speed': round(data['wind']['speed'] * 3.6, 1),  # m/s to km/h
                'condition': data['weather'][0]['main'],
                'description': data['weather'][0]['description'].capitalize(),
                'icon': data['weather'][0]['icon'],
                'timestamp': datetime.now().isoformat()
            }
            
            # Determinar emoción basada en clima
            weather_data['emotion'] = self.determine_weather_emotion(weather_data)
            
            self.current_weather = weather_data
            return weather_data
            
        except Exception as e:
            print(f"🌤️ Error obteniendo datos climáticos: {e}")
            return self.current_weather or {
                'city': city,
                'temp': 22.5,
                'condition': 'Clear',
                'emotion': 'calm',
                'timestamp': datetime.now().isoformat()
            }
    
    def determine_weather_emotion(self, weather_data):
        """Determina la emoción basada en las condiciones climáticas"""
        temp = weather_data['temp']
        condition = weather_data['condition']
        
        for emotion, thresholds in WEATHER_EMOTION_THRESHOLDS.items():
            if thresholds['temp_min'] <= temp <= thresholds['temp_max'] and condition in thresholds['conditions']:
                return emotion
        return 'neutral'
    
    def get_tmb_data(self):
        """Obtiene datos de transporte público (simulado para ejemplo)"""
        try:
            # En producción, aquí iría la llamada a la API de TMB
            # Por ahora, datos simulados con variación realista
            next_buses = [
                {'line': 'V13', 'minutes': random.randint(2, 8)},
                {'line': 'H16', 'minutes': random.randint(3, 10)},
                {'line': '7', 'minutes': random.randint(1, 5)}
            ]
            
            tmb_data = {
                'stop_name': 'Plaça Catalunya',
                'stop_id': TMB_STOP_ID,
                'next_buses': next_buses,
                'timestamp': datetime.now().isoformat(),
                'emotion': 'energetic' if any(bus['minutes'] < 3 for bus in next_buses) else 'calm'
            }
            
            self.current_tmb = tmb_data
            return tmb_data
            
        except Exception as e:
            print(f"🚌 Error obteniendo datos TMB: {e}")
            return self.current_tmb or {
                'stop_name': 'Plaça Catalunya',
                'next_buses': [{'line': 'V13', 'minutes': 5}],
                'emotion': 'calm',
                'timestamp': datetime.now().isoformat()
            }
    
    def simulate_pulse_data(self):
        """Simula datos de pulso cardíaco con variación realista"""
        base_pulse = 72
        
        # Variación según hora del día
        hour = datetime.now().hour
        if 6 <= hour < 9:  # Mañana
            base_pulse += 5
        elif 12 <= hour < 14:  # Mediodía
            base_pulse += 3
        elif 19 <= hour < 22:  # Noche
            base_pulse -= 2
        
        # Variación aleatoria
        variation = random.uniform(-3, 3)
        stress_factor = random.choice([0, 0, 1, 0, 2])  # Factor de estrés ocasional
        
        self.current_pulse = int(base_pulse + variation + stress_factor)
        
        pulse_data = {
            'bpm': self.current_pulse,
            'quality': 'good' if 50 <= self.current_pulse <= 100 else 'warning',
            'timestamp': datetime.now().isoformat(),
            'emotion': self.determine_pulse_emotion(self.current_pulse)
        }
        
        return pulse_data
    
    def determine_pulse_emotion(self, bpm):
        """Determina emoción basada en ritmo cardíaco"""
        if bpm < 60:
            return 'calm'
        elif 60 <= bpm <= 80:
            return 'neutral'
        elif 80 < bpm <= 100:
            return 'energetic'
        else:
            return 'anxious'
    
    def publish_weather_data(self):
        """Publica datos climáticos periódicamente"""
        while True:
            weather_data = self.get_weather_data()
            if weather_data:
                self.client.publish(CLIMA_TOPIC, json.dumps(weather_data), qos=1, retain=True)
                print(f"🌤️ Datos climáticos publicados: {weather_data['temp']}°C, {weather_data['condition']}")
            time.sleep(300)  # Actualizar cada 5 minutos
    
    def publish_tmb_data(self):
        """Publica datos de transporte periódicamente"""
        while True:
            tmb_data = self.get_tmb_data()
            if tmb_data:
                self.client.publish(TMB_TOPIC, json.dumps(tmb_data), qos=1, retain=True)
                print(f"🚌 Datos TMB publicados: {len(tmb_data['next_buses'])} buses próximos")
            time.sleep(60)  # Actualizar cada minuto
    
    def publish_pulse_data(self):
        """Publica datos de pulso continuamente"""
        while True:
            pulse_data = self.simulate_pulse_data()
            self.client.publish(PULSE_TOPIC, json.dumps(pulse_data), qos=0)
            print(f"💓 Pulso publicado: {pulse_data['bpm']} BPM - {pulse_data['emotion']}")
            time.sleep(2)  # Actualizar cada 2 segundos
    
    def start(self):
        """Inicia el publisher"""
        print("🚀 Iniciando Emotions Publisher...")
        
        try:
            self.client.connect(MQTT_BROKER, MQTT_PORT, 60)
            self.client.loop_start()
            
            # Iniciar hilos para cada tipo de datos
            threading.Thread(target=self.publish_weather_data, daemon=True).start()
            threading.Thread(target=self.publish_tmb_data, daemon=True).start()
            threading.Thread(target=self.publish_pulse_data, daemon=True).start()
            
            print("✅ Publisher iniciado correctamente")
            print("📡 Publicando en tópicos:")
            print(f"   - Clima: {CLIMA_TOPIC}")
            print(f"   - TMB: {TMB_TOPIC}")
            print(f"   - Pulso: {PULSE_TOPIC}")
            
            # Mantener el programa en ejecución
            while True:
                time.sleep(1)
                
        except KeyboardInterrupt:
            print("\n🛑 Deteniendo publisher...")
        except Exception as e:
            print(f"❌ Error crítico: {e}")
        finally:
            self.client.loop_stop()
            self.client.disconnect()
            print("🔌 Conexión MQTT cerrada")

if __name__ == "__main__":
    publisher = EmotionsPublisher()
    publisher.start()