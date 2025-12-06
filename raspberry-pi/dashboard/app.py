"""
Dashboard Web para Monitoramento de Dados do Sensor
Sistema IoT - Estação Meteorológica
"""

from flask import Flask, render_template, jsonify
import paho.mqtt.client as mqtt
import json
from datetime import datetime
from collections import deque
import threading

app = Flask(__name__)

# Armazenamento de dados (em produção, usar banco de dados)
data_history = {
    'temperature': deque(maxlen=100),
    'humidity': deque(maxlen=100),
    'soil_moisture': deque(maxlen=100),
    'timestamps': deque(maxlen=100)
}

# Dados atuais
current_data = {
    'temperature': 0.0,
    'humidity': 0.0,
    'soil_moisture': 0,
    'relay_status': 'OFF',
    'status': 'offline',
    'last_update': None
}

# Lock para thread safety
data_lock = threading.Lock()

# Configuração MQTT
MQTT_BROKER = 'localhost'
MQTT_PORT = 1883
MQTT_TOPICS = [
    'sensor/temperature',
    'sensor/humidity',
    'sensor/soil_moisture',
    'actuator/relay_status',
    'sensor/status'
]

# Cliente MQTT para publicar comandos
mqtt_publisher = mqtt.Client()

def on_connect(client, userdata, flags, rc):
    """Callback quando conecta ao broker MQTT"""
    if rc == 0:
        print("✅ Conectado ao broker MQTT")
        # Subscrever aos tópicos
        for topic in MQTT_TOPICS:
            client.subscribe(topic)
            print(f"📡 Inscrito no tópico: {topic}")
        # Subscrever também ao tópico de controle (para receber confirmações)
        client.subscribe('actuator/relay_control')
    else:
        print(f"❌ Falha na conexão MQTT. Código: {rc}")

def on_message(client, userdata, msg):
    """Callback quando recebe mensagem MQTT"""
    global current_data, data_history
    
    topic = msg.topic
    payload = msg.payload.decode('utf-8')
    timestamp = datetime.now()
    
    try:
        with data_lock:
            if topic == 'sensor/temperature':
                temperature = float(payload)
                current_data['temperature'] = temperature
                data_history['temperature'].append(temperature)
                data_history['timestamps'].append(timestamp.isoformat())
                
            elif topic == 'sensor/humidity':
                humidity = float(payload)
                current_data['humidity'] = humidity
                data_history['humidity'].append(humidity)
                
            elif topic == 'sensor/soil_moisture':
                soil_moisture = int(payload)
                current_data['soil_moisture'] = soil_moisture
                data_history['soil_moisture'].append(soil_moisture)
                if len(data_history['timestamps']) < len(data_history['soil_moisture']):
                    data_history['timestamps'].append(timestamp.isoformat())
                
            elif topic == 'actuator/relay_status':
                current_data['relay_status'] = payload.upper()
                
            elif topic == 'sensor/status':
                current_data['status'] = payload
                
            current_data['last_update'] = timestamp.strftime('%Y-%m-%d %H:%M:%S')
            
        print(f"📨 [{topic}] {payload}")
        
    except ValueError as e:
        print(f"⚠️ Erro ao processar mensagem: {e}")

# Configurar cliente MQTT
mqtt_client = mqtt.Client()
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message

# Conectar ao broker
try:
    mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
    mqtt_client.loop_start()
    
    # Conectar publisher para enviar comandos
    mqtt_publisher.connect(MQTT_BROKER, MQTT_PORT, 60)
    mqtt_publisher.loop_start()
except Exception as e:
    print(f"❌ Erro ao conectar ao broker MQTT: {e}")

@app.route('/')
def index():
    """Página principal do dashboard"""
    return render_template('index.html')

@app.route('/api/data')
def get_data():
    """API para obter dados atuais"""
    with data_lock:
        return jsonify(current_data)

@app.route('/api/history')
def get_history():
    """API para obter histórico de dados"""
    with data_lock:
        return jsonify({
            'temperature': list(data_history['temperature']),
            'humidity': list(data_history['humidity']),
            'soil_moisture': list(data_history['soil_moisture']),
            'timestamps': list(data_history['timestamps'])
        })

@app.route('/api/relay/control', methods=['POST'])
def control_relay():
    """API para controlar o relé"""
    from flask import request
    try:
        data = request.get_json()
        command = data.get('command', '').upper()
        
        if command in ['ON', 'OFF', 'AUTO']:
            topic = 'actuator/relay_control'
            mqtt_publisher.publish(topic, command, qos=1)
            return jsonify({'status': 'success', 'command': command})
        else:
            return jsonify({'status': 'error', 'message': 'Comando inválido'}), 400
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    print("🚀 Iniciando servidor Flask...")
    print("📊 Dashboard disponível em: http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)

