#!/usr/bin/env python3
"""
Visualización Maestra en Pygame con soporte Fullscreen para Raspberry Pi
"""
import pygame
import json
import time
import math
import paho.mqtt.client as mqtt
import threading
from api_keys import *

class MasterVisual:
    def __init__(self):
        pygame.init()
        
        # Configuración de pantalla (Modo ventana o Pantalla completa)
        if FULLSCREEN:
            self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
            pygame.mouse.set_visible(False) # Ocultar ratón
            self.width, self.height = self.screen.get_size()
        else:
            self.screen = pygame.display.set_mode((DISPLAY_WIDTH, DISPLAY_HEIGHT))
            pygame.display.set_caption("Emotions-in Monitor")
            self.width, self.height = DISPLAY_WIDTH, DISPLAY_HEIGHT

        self.clock = pygame.time.Clock()
        
        # Gestión de fuentes robusta
        try:
            self.font_s = pygame.font.Font(FONT_PATH, 20)
            self.font_m = pygame.font.Font(FONT_PATH, 28)
            self.font_l = pygame.font.Font(FONT_PATH, 42)
            self.font_xl = pygame.font.Font(FONT_PATH, 64)
        except:
            print("⚠️ Fuente no encontrada, usando por defecto")
            self.font_s = pygame.font.SysFont(None, 24)
            self.font_m = pygame.font.SysFont(None, 32)
            self.font_l = pygame.font.SysFont(None, 48)
            self.font_xl = pygame.font.SysFont(None, 72)

        # Colores y Estado
        self.emotion_colors = {
            'happy': (255, 200, 50), 'calm': (100, 180, 255),
            'energetic': (50, 220, 100), 'melancholic': (150, 100, 255),
            'anxious': (255, 80, 80), 'neutral': (200, 200, 200)
        }
        self.data = {'weather': None, 'tmb': None, 'pulse': None, 'global_emotion': 'neutral'}

        # MQTT
        self.client = mqtt.Client(client_id="master_visual")
        if MQTT_PASSWORD and MQTT_PASSWORD != "secure_password_here":
            self.client.username_pw_set(MQTT_USER, MQTT_PASSWORD)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

    def on_connect(self, client, userdata, flags, rc):
        print(f"✅ [Visual] Conectado a MQTT. Suscribiendo...")
        client.subscribe([(CLIMA_TOPIC, 0), (TMB_TOPIC, 0), (PULSE_TOPIC, 0)])

    def on_message(self, client, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode())
            if msg.topic == CLIMA_TOPIC: self.data['weather'] = payload
            elif msg.topic == TMB_TOPIC: self.data['tmb'] = payload
            elif msg.topic == PULSE_TOPIC: self.data['pulse'] = payload
            self.update_emotion()
        except Exception as e:
            print(f"Error decoding: {e}")

    def update_emotion(self):
        # Lógica simple: El pulso domina, si no, el clima
        if self.data['pulse']: 
            self.data['global_emotion'] = self.data['pulse'].get('emotion', 'neutral')
        elif self.data['weather']:
            self.data['global_emotion'] = self.data['weather'].get('emotion', 'neutral')

    def draw_text(self, text, font, color, x, y, align="left"):
        surface = font.render(text, True, color)
        rect = surface.get_rect()
        if align == "center": rect.center = (x, y)
        elif align == "right": rect.topright = (x, y)
        else: rect.topleft = (x, y)
        self.screen.blit(surface, rect)

    def draw_panels(self):
        margin = 20
        col_width = (self.width - (margin * 4)) / 3
        
        self.draw_card(margin, 100, col_width, 300, self.data['weather'], "Clima")
        self.draw_card(margin*2 + col_width, 100, col_width, 300, self.data['tmb'], "Transporte")
        self.draw_card(margin*3 + col_width*2, 100, col_width, 300, self.data['pulse'], "Pulso")

    def draw_card(self, x, y, w, h, data, title):
        color = (100, 100, 100)
        content = ["Esperando datos..."]
        
        if data:
            emo = data.get('emotion', 'neutral')
            color = self.emotion_colors.get(emo, (200,200,200))
            
            if title == "Clima":
                content = [
                    f"{data.get('temp',0)}°C", 
                    data.get('condition','--'),
                    data.get('city','--')
                ]
            elif title == "Transporte":
                buses = data.get('next_buses', [])
                content = [f"{b['line']}: {b['minutes']} min" for b in buses[:3]]
                if not content: content = ["Sin buses próximos"]
            elif title == "Pulso":
                content = [f"{data.get('bpm',0)} BPM", data.get('quality','--')]

        pygame.draw.rect(self.screen, (20, 25, 40), (x, y, w, h), border_radius=10)
        pygame.draw.rect(self.screen, color, (x, y, w, h), 2, border_radius=10)
        
        self.draw_text(title, self.font_m, color, x + 15, y + 15)
        
        start_y = y + 60
        for line in content:
            self.draw_text(str(line), self.font_l, (255,255,255), x + 20, start_y)
            start_y += 50

    def run(self):
        try:
            self.client.connect(MQTT_BROKER, MQTT_PORT, 60)
            self.client.loop_start()
            
            running = True
            while running:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT: running = False
                    if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE: running = False

                self.screen.fill(BG_COLOR)
                
                emo = self.data['global_emotion'].upper()
                c = self.emotion_colors.get(self.data['global_emotion'], (200,200,200))
                self.draw_text(f"ESTADO: {emo}", self.font_xl, c, self.width//2, 50, "center")
                
                self.draw_panels()
                
                pygame.display.flip()
                self.clock.tick(30) # 30 FPS

        except Exception as e:
            print(f"Error Visual: {e}")
        finally:
            self.client.loop_stop()
            pygame.quit()

if __name__ == "__main__":
    MasterVisual().run()
    