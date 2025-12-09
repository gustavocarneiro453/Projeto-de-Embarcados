"""
Configurações da aplicação Flask + MQTT para o dashboard IoT.
"""

# =========================
# Configurações MQTT
# =========================

# IMPORTANTE: aqui vai o IP DO SEU PC (onde o Mosquitto está rodando)
# ipconfig mostrou: 192.168.3.11
MQTT_BROKER = "192.168.3.11"
MQTT_PORT = 1883

# Tópicos de sensores (batendo com a ESP32)
MQTT_TOPIC_SOIL_MOISTURE = "sensor/soil_moisture"
MQTT_TOPIC_STATUS        = "sensor/status"

# Tópicos de atuadores (relé)
MQTT_TOPIC_RELAY_STATUS  = "actuator/relay_status"   # status atual do relé
MQTT_TOPIC_RELAY_CONTROL = "actuator/relay_control"  # comandos ON/OFF/AUTO

# Lista de tópicos que o dashboard deve assinar
MQTT_TOPICS = [
    MQTT_TOPIC_SOIL_MOISTURE,
    MQTT_TOPIC_RELAY_STATUS,
    MQTT_TOPIC_STATUS,
]

# =========================
# Configurações do Flask
# =========================

FLASK_HOST = "0.0.0.0"
FLASK_PORT = 5000
FLASK_DEBUG = True   # se quiser evitar reloader duplicado, pode trocar para False depois

# =========================
# Histórico em memória
# =========================

MAX_HISTORY_SIZE = 100
