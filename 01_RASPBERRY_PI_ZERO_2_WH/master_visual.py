#!/usr/bin/env python3
"""
Visualización maestra para Emotions-in
Muestra los datos de todos los sensores en una interfaz unificada
"""

import pygame
import json
import time
from datetime import datetime
import paho.mqtt.client as mqtt
import threading
from api_keys import *

class MasterVisual:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Emotions-in - Visualización Maestra")
        
        # Configuración de pantalla
        self.screen = pygame.display.set_mode((DISPLAY_WIDTH, DISPLAY_HEIGHT))
        self.clock = pygame.time.Clock()
        self.font_small = pygame.font.Font(FONT_PATH, 20)
        self.font_medium = pygame.font.Font(FONT_PATH, 28)
        self.font_large = pygame.font.Font(FONT_PATH, 42)
        self.font_xlarge = pygame.font.Font(FONT_PATH, 64)
        
        # Colores emocionales
        self.emotion_colors = {
            'happy': (255, 200, 50),    # Amarillo brillante
            'calm': (100, 180, 255),    # Azul cielo
            'energetic': (50, 220, 100), # Verde vibrante
            'melancholic': (150, 100, 255), # Púrpura
            'anxious': (255, 80, 80),   # Rojo suave
            'neutral': (200, 200, 200)  # Gris
        }
        
        # Datos actuales
        self.weather_data = None
        self.tmb_data = None
        self.pulse_data = None
        self.current_emotion = 'neutral'
        
        # Configuración MQTT
        self.client = mqtt.Client(client_id="master_visual")
        self.client.username_pw_set(MQTT_USER, MQTT_PASSWORD)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        
        # FPS de actualización
        self.fps = 30
        
    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print("✅ Visualización conectada al broker MQTT")
            self.client.subscribe([(CLIMA_TOPIC, 1), (TMB_TOPIC, 1), (PULSE_TOPIC, 0)])
        else:
            print(f"❌ Error de conexión: {rc}")
    
    def on_message(self, client, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode())
            
            if msg.topic == CLIMA_TOPIC:
                self.weather_data = payload
            elif msg.topic == TMB_TOPIC:
                self.tmb_data = payload
            elif msg.topic == PULSE_TOPIC:
                self.pulse_data = payload
            
            # Determinar emoción global
            self.determine_global_emotion()
            
        except Exception as e:
            print(f"❌ Error procesando mensaje MQTT: {e}")
    
    def determine_global_emotion(self):
        """Determina la emoción global basada en todos los sensores"""
        emotions = []
        
        if self.weather_data and 'emotion' in self.weather_data:
            emotions.append(self.weather_data['emotion'])
        
        if self.tmb_data and 'emotion' in self.tmb_data:
            emotions.append(self.tmb_data['emotion'])
        
        if self.pulse_data and 'emotion' in self.pulse_data:
            emotions.append(self.pulse_data['emotion'])
        
        if not emotions:
            self.current_emotion = 'neutral'
            return
        
        # Dar más peso al pulso (emoción en tiempo real)
        emotion_weights = {}
        for emotion in emotions:
            emotion_weights[emotion] = emotion_weights.get(emotion, 0) + 1
        
        # Si hay pulso, darle doble peso
        if self.pulse_data and 'emotion' in self.pulse_data:
            pulse_emotion = self.pulse_data['emotion']
            emotion_weights[pulse_emotion] = emotion_weights.get(pulse_emotion, 0) + 1
        
        # Seleccionar emoción dominante
        self.current_emotion = max(emotion_weights, key=emotion_weights.get)
    
    def draw_weather_panel(self, x, y, width, height):
        """Dibuja el panel de clima"""
        if not self.weather_data:
            return
        
        # Fondo del panel
        panel_color = (*self.emotion_colors.get(self.weather_data.get('emotion', 'neutral'), (200, 200, 200)), 180)
        pygame.draw.rect(self.screen, panel_color, (x, y, width, height), border_radius=15)
        pygame.draw.rect(self.screen, (255, 255, 255), (x, y, width, height), 2, border_radius=15)
        
        # Icono y temperatura
        temp_text = self.font_xlarge.render(f"{self.weather_data['temp']}°C", True, (255, 255, 255))
        self.screen.blit(temp_text, (x + 20, y + 20))
        
        # Condición
        condition_text = self.font_medium.render(self.weather_data['condition'], True, (255, 255, 255))
        self.screen.blit(condition_text, (x + 20, y + 100))
        
        # Ciudad
        city_text = self.font_medium.render(self.weather_data['city'], True, (255, 255, 255))
        self.screen.blit(city_text, (x + 20, y + 140))
        
        # Humedad y viento
        stats_text = self.font_small.render(
            f"Humedad: {self.weather_data['humidity']}% | Viento: {self.weather_data['wind_speed']} km/h", 
            True, (255, 255, 255)
        )
        self.screen.blit(stats_text, (x + 20, y + 180))
        
        # Emoción
        emotion_text = self.font_medium.render(f"Emoción: {self.weather_data['emotion'].capitalize()}", True, (255, 255, 255))
        self.screen.blit(emotion_text, (x + 20, y + 220))
    
    def draw_tmb_panel(self, x, y, width, height):
        """Dibuja el panel de transporte"""
        if not self.tmb_data:
            return
        
        panel_color = (*self.emotion_colors.get(self.tmb_data.get('emotion', 'neutral'), (200, 200, 200)), 180)
        pygame.draw.rect(self.screen, panel_color, (x, y, width, height), border_radius=15)
        pygame.draw.rect(self.screen, (255, 255, 255), (x, y, width, height), 2, border_radius=15)
        
        # Título
        title_text = self.font_large.render("🚌 Próximos Buses", True, (255, 255, 255))
        self.screen.blit(title_text, (x + 20, y + 20))
        
        # Parada
        stop_text = self.font_medium.render(f"Parada: {self.tmb_data['stop_name']}", True, (255, 255, 255))
        self.screen.blit(stop_text, (x + 20, y + 80))
        
        # Buses
        y_pos = y + 130
        for bus in self.tmb_data.get('next_buses', [])[:3]:
            bus_text = self.font_medium.render(f"Línea {bus['line']}: {bus['minutes']} min", True, (255, 255, 255))
            self.screen.blit(bus_text, (x + 20, y_pos))
            y_pos += 45
        
        # Emoción
        emotion_text = self.font_medium.render(f"Emoción: {self.tmb_data['emotion'].capitalize()}", True, (255, 255, 255))
        self.screen.blit(emotion_text, (x + 20, y + height - 60))
    
    def draw_pulse_panel(self, x, y, width, height):
        """Dibuja el panel de pulso cardíaco"""
        panel_color = (*self.emotion_colors.get(self.pulse_data.get('emotion', 'neutral') if self.pulse_data else 'neutral', (200, 200, 200)), 180)
        pygame.draw.rect(self.screen, panel_color, (x, y, width, height), border_radius=15)
        pygame.draw.rect(self.screen, (255, 255, 255), (x, y, width, height), 2, border_radius=15)
        
        # Título
        title_text = self.font_large.render("💓 Pulso Cardíaco", True, (255, 255, 255))
        self.screen.blit(title_text, (x + 20, y + 20))
        
        if self.pulse_data:
            # BPM grande
            bpm_text = self.font_xlarge.render(f"{self.pulse_data['bpm']} BPM", True, (255, 255, 255))
            self.screen.blit(bpm_text, (x + 20, y + 80))
            
            # Calidad
            quality_color = (100, 255, 100) if self.pulse_data['quality'] == 'good' else (255, 150, 50)
            quality_text = self.font_medium.render(f"Calidad: {self.pulse_data['quality'].capitalize()}", True, quality_color)
            self.screen.blit(quality_text, (x + 20, y + 160))
            
            # Gráfico de pulso simulado
            self.draw_pulse_wave(x + 20, y + 210, width - 40, 80)
            
            # Emoción
            emotion_text = self.font_medium.render(f"Emoción: {self.pulse_data['emotion'].capitalize()}", True, (255, 255, 255))
            self.screen.blit(emotion_text, (x + 20, y + 300))
        else:
            # Mensaje de espera
            wait_text = self.font_medium.render("Esperando datos...", True, (255, 255, 255))
            self.screen.blit(wait_text, (x + 20, y + 150))
    
    def draw_pulse_wave(self, x, y, width, height):
        """Dibuja una onda de pulso simulada"""
        current_time = time.time() * 2
        points = []
        
        # Generar puntos para la onda
        for i in range(width):
            t = current_time + i * 0.05
            # Onda principal con variación basada en BPM
            base_freq = self.pulse_data['bpm'] / 60 if self.pulse_data else 1.2
            y_pos = y + height/2 + 30 * (
                0.7 * math.sin(t * base_freq) + 
                0.3 * math.sin(t * base_freq * 3 + 1.57)
            )
            points.append((x + i, y_pos))
        
        # Dibujar la línea de pulso
        pygame.draw.lines(self.screen, (255, 255, 255), False, points, 2)
    
    def draw_global_emotion(self):
        """Dibuja el estado emocional global"""
        emotion_color = self.emotion_colors.get(self.current_emotion, (200, 200, 200))
        
        # Círculo emocional
        center_x, center_y = DISPLAY_WIDTH - 120, 80
        pygame.draw.circle(self.screen, emotion_color, (center_x, center_y), 50)
        pygame.draw.circle(self.screen, (255, 255, 255), (center_x, center_y), 50, 2)
        
        # Texto de emoción
        emotion_text = self.font_medium.render(self.current_emotion.capitalize(), True, (255, 255, 255))
        text_rect = emotion_text.get_rect(center=(center_x, center_y + 70))
        self.screen.blit(emotion_text, text_rect)
        
        # Símbolo según emoción
        symbols = {
            'happy': '☀️',
            'calm': '☁️',
            'energetic': '⚡',
            'melancholic': '🌧️',
            'anxious': '💨',
            'neutral': '💭'
        }
        
        symbol_font = pygame.font.Font(None, 48)
        symbol_text = symbol_font.render(symbols.get(self.current_emotion, '💭'), True, (255, 255, 255))
        symbol_rect = symbol_text.get_rect(center=(center_x, center_y))
        self.screen.blit(symbol_text, symbol_rect)
    
    def draw_header(self):
        """Dibuja el encabezado con fecha y hora"""
        now = datetime.now()
        date_text = self.font_medium.render(now.strftime("%A, %d de %B de %Y"), True, (255, 255, 255))
        time_text = self.font_xlarge.render(now.strftime("%H:%M:%S"), True, (255, 255, 255))
        
        self.screen.blit(date_text, (20, 20))
        self.screen.blit(time_text, (20, 60))
    
    def draw_footer(self):
        """Dibuja el pie de página con información del sistema"""
        status_text = self.font_small.render("MQTT: Conectado ✅ | Fuente de alimentación: Estable 🔋", True, (200, 200, 200))
        self.screen.blit(status_text, (20, DISPLAY_HEIGHT - 30))
    
    def run(self):
        """Bucle principal de la visualización"""
        print("🎨 Iniciando visualización maestra...")
        
        try:
            self.client.connect(MQTT_BROKER, MQTT_PORT, 60)
            self.client.loop_start()
            
            running = True
            last_time = time.time()
            
            while running:
                # Manejar eventos
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False
                    elif event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            running = False
                
                # Actualizar FPS
                current_time = time.time()
                delta_time = current_time - last_time
                last_time = current_time
                
                # Dibujar fondo
                self.screen.fill(BG_COLOR)
                
                # Dibujar interfaz
                self.draw_header()
                self.draw_global_emotion()
                
                # Panel de clima (izquierda)
                self.draw_weather_panel(20, 150, 350, 300)
                
                # Panel de transporte (centro)
                self.draw_tmb_panel(390, 150, 350, 300)
                
                # Panel de pulso (derecha inferior)
                self.draw_pulse_panel(20, 470, 720, 220)
                
                self.draw_footer()
                
                # Actualizar pantalla
                pygame.display.flip()
                self.clock.tick(self.fps)
                
                # Mantener FPS constante
                if delta_time < 1/self.fps:
                    time.sleep(1/self.fps - delta_time)
                
        except KeyboardInterrupt:
            print("\n🛑 Visualización detenida por usuario")
        except Exception as e:
            print(f"❌ Error en visualización: {e}")
        finally:
            self.client.loop_stop()
            self.client.disconnect()
            pygame.quit()
            print("✅ Visualización maestra finalizada")

if __name__ == "__main__":
    import math  # Necesario para la onda de pulso
    visual = MasterVisual()
    visual.run()