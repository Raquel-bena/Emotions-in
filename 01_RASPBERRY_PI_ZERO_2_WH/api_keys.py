# Claves API y configuración sensible
# ¡NUNCA subas este archivo a GitHub!

WEATHER_API_KEY = "your_openweather_api_key_here"
OPENWEATHER_URL = "https://api.openweathermap.org/data/2.5/weather"

# Configuración MQTT
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_USER = "emotions_user"
MQTT_PASSWORD = "secure_password_here"

# Tópicos MQTT
CLIMA_TOPIC = "emotions/clima"
TMB_TOPIC = "emotions/tmb"
PULSE_TOPIC = "emotions/pulse"

# Configuración TMB (Barcelona)
TMB_APP_ID = "your_tmb_app_id"
TMB_APP_KEY = "your_tmb_app_key"
TMB_STOP_ID = "791"  # Ejemplo: Parada de metro Plaça Catalunya

# Configuración visualización
DISPLAY_WIDTH = 800
DISPLAY_HEIGHT = 480
BG_COLOR = (10, 15, 30)  # Azul oscuro
FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

# Umbrales para emociones basadas en clima
WEATHER_EMOTION_THRESHOLDS = {
    "happy": {"temp_min": 18, "temp_max": 28, "conditions": ["Clear", "Clouds"]},
    "calm": {"temp_min": 12, "temp_max": 22, "conditions": ["Clouds", "Drizzle"]},
    "energetic": {"temp_min": 22, "temp_max": 35, "conditions": ["Clear"]},
    "melancholic": {"temp_min": -5, "temp_max": 12, "conditions": ["Rain", "Snow", "Thunderstorm"]}
}