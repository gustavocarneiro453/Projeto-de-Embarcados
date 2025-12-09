"""
Dashboard Web para Monitoramento de Umidade do Solo
Sistema IoT - Irrigação Automática
"""

from datetime import datetime
from collections import deque
import threading

from flask import Flask, render_template, jsonify, request
import paho.mqtt.client as mqtt

import config as app_config

app = Flask(__name__)

# =========================
# Estado em memória
# =========================

HISTORY_SIZE = getattr(app_config, "MAX_HISTORY_SIZE", 100)

data_history = {
    "soil_moisture": deque(maxlen=HISTORY_SIZE),
    "timestamps": deque(maxlen=HISTORY_SIZE),
}

current_data = {
    "soil_moisture": 0,
    "relay_status": "OFF",
    "status": "offline",
    "last_update": None,
}

data_lock = threading.Lock()

# =========================
# MQTT – configurações
# =========================

MQTT_BROKER = getattr(app_config, "MQTT_BROKER", "localhost")
MQTT_PORT = getattr(app_config, "MQTT_PORT", 1883)

DEFAULT_MQTT_TOPICS = [
    getattr(app_config, "MQTT_TOPIC_SOIL_MOISTURE", "sensor/soil_moisture"),
    getattr(app_config, "MQTT_TOPIC_RELAY_STATUS", "actuator/relay_status"),
    getattr(app_config, "MQTT_TOPIC_STATUS", "sensor/status"),
]

MQTT_TOPICS = getattr(app_config, "MQTT_TOPICS", DEFAULT_MQTT_TOPICS)

mqtt_client = mqtt.Client()      # assina tópicos (dados vindo da ESP32)
mqtt_publisher = mqtt.Client()   # publica comandos (atuador/relay_control)

# =========================
# Callbacks MQTT
# =========================

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("✅ Conectado ao broker MQTT")
        for topic in MQTT_TOPICS:
            client.subscribe(topic)
            print(f"📡 Inscrito no tópico: {topic}")
    else:
        print(f"❌ Falha na conexão MQTT. Código: {rc}")


def on_message(client, userdata, msg):
    topic = msg.topic
    payload = msg.payload.decode("utf-8", errors="ignore")
    timestamp = datetime.now()

    try:
        with data_lock:
            # Umidade do solo (vindo da ESP em 0–100)
            if topic == app_config.MQTT_TOPIC_SOIL_MOISTURE:
                try:
                    value = int(payload)
                except ValueError:
                    value = 0
                current_data["soil_moisture"] = value
                data_history["soil_moisture"].append(value)
                data_history["timestamps"].append(timestamp.isoformat())

            # Status do relé (ON/OFF/AUTO)
            elif topic == app_config.MQTT_TOPIC_RELAY_STATUS:
                current_data["relay_status"] = payload.upper()

            # Status geral da ESP32 (online/offline)
            elif topic == app_config.MQTT_TOPIC_STATUS:
                current_data["status"] = payload.lower()

            # Sempre que chega algo reconhecido, atualiza last_update
            current_data["last_update"] = timestamp.strftime("%Y-%m-%d %H:%M:%S")

        print(f"📨 [{topic}] {payload}")

    except Exception as exc:
        print(f"⚠️ Erro ao processar mensagem MQTT: {exc}")

# =========================
# Inicialização MQTT
# =========================

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
        return jsonify(current_data)


@app.route("/api/history")
def get_history():
    with data_lock:
        return jsonify(
            {
                "soil_moisture": list(data_history["soil_moisture"]),
                "timestamps": list(data_history["timestamps"]),
            }
        )


@app.route("/api/relay/control", methods=["POST"])
def control_relay():
    """
    Recebe comando do dashboard (ON/OFF/AUTO) e publica em actuator/relay_control,
    que é o tópico que a ESP32 está assinando.
    """
    try:
        data = request.get_json(silent=True) or {}
        command = str(data.get("command", "")).upper()

        if command not in {"ON", "OFF", "AUTO"}:
            return jsonify(
                {"status": "error", "message": "Comando inválido"}
            ), 400

        mqtt_publisher.publish(app_config.MQTT_TOPIC_RELAY_CONTROL, command, qos=1)
        print(f"📤 Enviado comando para relé: {command}")
        return jsonify({"status": "success", "command": command})

    except Exception as exc:
        return jsonify({"status": "error", "message": str(exc)}), 500


if __name__ == "__main__":
    host = getattr(app_config, "FLASK_HOST", "0.0.0.0")
    port = getattr(app_config, "FLASK_PORT", 5000)
    debug = getattr(app_config, "FLASK_DEBUG", True)

    print("🚀 Iniciando servidor Flask...")
    print(f"📊 Dashboard disponível em: http://{host}:{port}")
    app.run(host=host, port=port, debug=debug)
