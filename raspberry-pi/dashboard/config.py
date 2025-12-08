"""
Configurações da aplicação Flask + MQTT para o dashboard IoT.

Edite este arquivo para ajustar o ambiente (broker MQTT, host do Flask, etc.).
"""

# =========================
# Configurações MQTT
# =========================

MQTT_BROKER = "localhost"
MQTT_PORT = 1883

# Tópico do sensor de umidade do solo
MQTT_TOPIC_SOIL_MOISTURE = "sensor/soil_moisture"

# Tópico opcional de status geral do dispositivo (online/offline)
MQTT_TOPIC_STATUS = "sensor/status"

# Tópicos de atuadores (relé)
MQTT_TOPIC_RELAY_STATUS = "actuator/relay_status"
MQTT_TOPIC_RELAY_CONTROL = "actuator/relay_control"

# Tópicos que o dashboard assina
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
FLASK_DEBUG = True  # Em produção, idealmente False

# =========================
# Configurações de histórico
# =========================

MAX_HISTORY_SIZE = 100
