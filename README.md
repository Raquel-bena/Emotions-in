# Emotions in Transit

**Emotions in Transit** is an interactive generative installation that transforms Barcelona's public transport data (TMB) and real-time weather conditions into an audiovisual experience.

The system interprets the "mood" of the city based on the flow of buses/metro and weather patterns, visualizing it through LED arrays, physical displays, and projection mapping.

## Project Structure

* **`01_RASPBERRY_PI_ZERO_2_WH/`**: **The Brain**. Python scripts that:
    * Fetch data from APIs (TMB & OpenWeatherMap).
    * Process the logic for the city's "emotions".
    * Publish commands via MQTT to microcontrollers.
* **`02_ESP32_CLIMA_DISPLAY/`**: Arduino code for the ESP32 controlling the weather visualization.
* **`03_ESP32_TMB_DISPLAY/`**: Arduino code for the ESP32 visualizing transport data.
* **`04_ESP32_RAW_PULSE_LEDS/`**: Control for LED strips simulating the city's "heartbeat".
* **`Instalacion_Final/`**: Flask Web Server for the control interface and web-based visualization.
* **`touchdesigner/`**: `.toe` files for complex visual generation and projection.
* **`mosquitto_setup/`**: Configuration files for the MQTT Broker.

##  Tech Stack

* **Hardware:** Raspberry Pi Zero 2 WH, ESP32 Microcontrollers (x3), Sensors, LED Strips.
* **Software:** Python 3, C++ (Arduino), TouchDesigner.
* **Communication:** MQTT (Mosquitto Broker).
* **APIs:** TMB (Transports Metropolitans de Barcelona), OpenWeatherMap.

## Installation (Raspberry Pi)

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/Raquel-bena/Emotions-in.git](https://github.com/Raquel-bena/Emotions-in.git)
    cd Emotions-in
    ```

2.  **Set up Virtual Environment:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```

3.  **Configure API Keys:**
    * Rename `api_keys_example.py` to `api_keys.py` inside the `01_RASPBERRY...` folder.
    * Add your TMB and OpenWeatherMap credentials.

4.  **Run the System:**
    ```bash
    python 01_RASPBERRY_PI_ZERO_2_WH/main_publisher.py
    ```

## Author
Project developed by **Raquel Bena**.