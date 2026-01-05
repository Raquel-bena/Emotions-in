from pythonosc import udp_client
import time
import random

# Configuración: IP de tu PC y puerto 8000
client = udp_client.SimpleUDPClient("127.0.0.1", 8000)

print("🚀 Motor de datos iniciado. Enviando a TouchDesigner...")

while True:
    # Datos basados en tu UI
    noise = random.uniform(37.0, 38.5) # Simula los 37.7 dB de tu imagen
    co2 = random.randint(95, 105)      # Simula los 99 ppm
    pulse = random.uniform(0.1, 0.9)   # Simula el nivel de metabolismo/ritmo
    
    # Enviamos los mensajes por OSC
    client.send_message("/noise", noise)
    client.send_message("/co2", co2)
    client.send_message("/pulse", pulse)
    
    time.sleep(0.05) # Enviamos rápido para que el movimiento sea fluido
    