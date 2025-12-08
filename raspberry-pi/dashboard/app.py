"""
Dashboard Web para Monitoramento de Dados do Sensor
Sistema IoT - Estação Meteorológica
"""

from datetime import datetime
from collections import deque
import threading

from flask import Flask, render_template, jsonify, request
import paho.mqtt.client as mqtt

app = Flask(__name__)

# =========================
# Configuração da aplicação
# =========================

try:
    import config as app_config
except ImportError:
    # Fallback simples se config.py não existir
    class app_config:
        MQTT_BROKER = "localhost"
        MQTT_PORT = 1883
        MQTT_TOPICS = [
            "sensor/temperature",
            "sensor/humidity",
            "sensor/soil_moisture",
            "actuator/relay_status",
            "sensor/status",
        ]
        FLASK_HOST = "0.0.0.0"
        FLASK_PORT = 5000
        FLASK_DEBUG = True
        MAX_HISTORY_SIZE = 100

HISTORY_SIZE = getattr(app_config, "MAX_HISTORY_SIZE", 100)

# =========================
# Estado em memória
# =========================

data_history = {
    "temperature": deque(maxlen=HISTORY_SIZE),
    "humidity": deque(maxlen=HISTORY_SIZE),
    "soil_moisture": deque(maxlen=HISTORY_SIZE),
    "timestamps": deque(maxlen=HISTORY_SIZE),
}

current_data = {
    "temperature": 0.0,
    "humidity": 0.0,
    "soil_moisture": 0,
    "relay_status": "OFF",
    "status": "offline",
    "last_update": None,
}

data_lock = threading.Lock()

# =========================
# Configuração MQTT
# =========================

DEFAULT_MQTT_TOPICS = [
    "sensor/temperature",
    "sensor/humidity",
    "sensor/soil_moisture",
    "actuator/relay_status",
    "sensor/status",
]

MQTT_BROKER = getattr(app_config, "MQTT_BROKER", "localhost")
MQTT_PORT = getattr(app_config, "MQTT_PORT", 1883)
MQTT_TOPICS = getattr(app_config, "MQTT_TOPICS", DEFAULT_MQTT_TOPICS)

# Cliente MQTT para publicação de comandos
mqtt_publisher = mqtt.Client()
mqtt_client = mqtt.Client()


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("✅ Conectado ao broker MQTT")
        for topic in MQTT_TOPICS:
            client.subscribe(topic)
            print(f"📡 Inscrito no tópico: {topic}")
        # Tópico de controle (confirmações/comandos)
        client.subscribe("actuator/relay_control")
    else:
        print(f"❌ Falha na conexão MQTT. Código: {rc}")


def on_message(client, userdata, msg):
    topic = msg.topic
    payload = msg.payload.decode("utf-8")
    timestamp = datetime.now()

    try:
        with data_lock:
            if topic == "sensor/temperature":
                value = float(payload)
                current_data["temperature"] = value
                data_history["temperature"].append(value)
                data_history["timestamps"].append(timestamp.isoformat())

            elif topic == "sensor/humidity":
                value = float(payload)
                current_data["humidity"] = value
                data_history["humidity"].append(value)

            elif topic == "sensor/soil_moisture":
                value = int(payload)
                current_data["soil_moisture"] = value
                data_history["soil_moisture"].append(value)
                if len(data_history["timestamps"]) < len(
                    data_history["soil_moisture"]
                ):
                    data_history["timestamps"].append(timestamp.isoformat())

            elif topic == "actuator/relay_status":
                current_data["relay_status"] = payload.upper()

            elif topic == "sensor/status":
                current_data["status"] = payload

            current_data["last_update"] = timestamp.strftime("%Y-%m-%d %H:%M:%S")

        print(f"📨 [{topic}] {payload}")

    except ValueError as exc:
        print(f"⚠️ Erro ao processar mensagem: {exc}")


mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message

try:
    mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
    mqtt_client.loop_start()

    mqtt_publisher.connect(MQTT_BROKER, MQTT_PORT, 60)
    mqtt_publisher.loop_start()
except Exception as exc:
    print(f"❌ Erro ao conectar ao broker MQTT: {exc}")

# =========================
# Rotas Flask
# =========================


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/data")
def get_data():
    with data_lock:
        payload = dict(current_data)
    return jsonify(payload)


@app.route("/api/history")
def get_history():
    with data_lock:
        history_payload = {
            "temperature": list(data_history["temperature"]),
            "humidity": list(data_history["humidity"]),
            "soil_moisture": list(data_history["soil_moisture"]),
            "timestamps": list(data_history["timestamps"]),
        }
    return jsonify(history_payload)


@app.route("/api/relay/control", methods=["POST"])
def control_relay():
    try:
        data = request.get_json(silent=True) or {}
        command = str(data.get("command", "")).upper()

        if command in {"ON", "OFF", "AUTO"}:
            topic = "actuator/relay_control"
            mqtt_publisher.publish(topic, command, qos=1)
            return jsonify({"status": "success", "command": command})

        return jsonify({"status": "error", "message": "Comando inválido"}), 400

    except Exception as exc:
        return jsonify({"status": "error", "message": str(exc)}), 500


if __name__ == "__main__":
    host = getattr(app_config, "FLASK_HOST", "0.0.0.0")
    port = getattr(app_config, "FLASK_PORT", 5000)
    debug = getattr(app_config, "FLASK_DEBUG", True)

    print("🚀 Iniciando servidor Flask...")
    print(f"📊 Dashboard disponível em: http://{host}:{port}")
    app.run(host=host, port=port, debug=debug)
