# Arquivo de configuração de exemplo
# Copie este arquivo para config.py e edite com suas configurações

# Configurações MQTT
MQTT_BROKER = 'localhost'  # IP do broker MQTT
MQTT_PORT = 1883

# Tópicos MQTT
MQTT_TOPICS = [
    'sensor/temperature',
    'sensor/humidity',
    'sensor/status'
]

# Configurações do Flask
FLASK_HOST = '0.0.0.0'  # Aceitar conexões de qualquer IP
FLASK_PORT = 5000
FLASK_DEBUG = True

# Configurações de histórico
MAX_HISTORY_SIZE = 100  # Número máximo de pontos no histórico

