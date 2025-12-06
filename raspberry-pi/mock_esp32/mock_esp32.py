#!/usr/bin/env python3
"""
Mock ESP32 - Simulador do Sistema de Irrigação
Este script simula o comportamento do ESP32, publicando dados de sensores
e recebendo comandos de controle do relé via MQTT
"""

import paho.mqtt.client as mqtt
import time
import random
import json
from datetime import datetime
import sys

# Verificar versão do paho-mqtt e importar CallbackAPIVersion se disponível
try:
    from paho.mqtt.client import CallbackAPIVersion
    PAHO_MQTT_V2 = True
    # Usar VERSION2 (mais recente, sem depreciação)
    CALLBACK_API_VERSION = CallbackAPIVersion.VERSION2
except ImportError:
    PAHO_MQTT_V2 = False
    CALLBACK_API_VERSION = None

# ==================== CONFIGURAÇÕES ====================

# Configurações MQTT
MQTT_BROKER = 'localhost'  # IP do broker MQTT (localhost se no mesmo Pi)
MQTT_PORT = 1883
MQTT_CLIENT_ID = 'ESP32_Mock_01'

# Tópicos MQTT
TOPIC_TEMPERATURE = "sensor/temperature"
TOPIC_HUMIDITY = "sensor/humidity"
TOPIC_SOIL_MOISTURE = "sensor/soil_moisture"
TOPIC_RELAY_STATUS = "actuator/relay_status"
TOPIC_RELAY_CONTROL = "actuator/relay_control"
TOPIC_STATUS = "sensor/status"

# Configurações de Simulação
SENSOR_INTERVAL = 5.0          # Publicar dados a cada 5 segundos
STATUS_INTERVAL = 30.0         # Publicar status a cada 30 segundos

# Valores iniciais dos sensores
current_temperature = 25.0      # Temperatura inicial (°C)
current_humidity = 60.0         # Umidade do ar inicial (%)
current_soil_moisture = 45      # Umidade do solo inicial (%)
relay_state = False              # Estado do relé (False = desligado)
auto_mode = True                # Modo automático

# Limites para simulação automática
SOIL_MOISTURE_THRESHOLD_LOW = 30
SOIL_MOISTURE_THRESHOLD_HIGH = 60

# ==================== FUNÇÕES MQTT ====================

def on_connect(client, userdata, flags, reason_code=None, properties=None):
    """Callback quando conecta ao broker MQTT"""
    # Compatibilidade com API v1 e v2
    if PAHO_MQTT_V2 and reason_code is not None:
        rc = reason_code.rc if hasattr(reason_code, 'rc') else reason_code
    else:
        # API v1 usa flags como código de retorno
        rc = flags if isinstance(flags, int) else 0
    
    if rc == 0:
        print("✅ Conectado ao broker MQTT!")
        print(f"📡 Broker: {MQTT_BROKER}:{MQTT_PORT}\n")
        
        # Subscrever ao tópico de controle do relé
        client.subscribe(TOPIC_RELAY_CONTROL)
        print(f"📥 Inscrito no tópico: {TOPIC_RELAY_CONTROL}")
        
        # Publicar status inicial
        publish_status(client, "online")
        publish_relay_status(client)
        
        print("\n🚀 Mock ESP32 iniciado!")
        print("=" * 50)
        print("📊 Publicando dados dos sensores...")
        print("💡 Use os comandos abaixo para controlar o relé:\n")
        print_help()
        
    else:
        print(f"❌ Falha na conexão MQTT. Código: {rc}")
        sys.exit(1)

def on_message(client, userdata, msg):
    """Callback quando recebe mensagem MQTT"""
    global relay_state, auto_mode
    
    topic = msg.topic
    payload = msg.payload.decode('utf-8')
    
    print(f"\n📨 Mensagem recebida:")
    print(f"   Tópico: {topic}")
    print(f"   Payload: {payload}")
    
    if topic == TOPIC_RELAY_CONTROL:
        if payload.upper() == "ON" or payload == "1" or payload.lower() == "true":
            relay_state = True
            auto_mode = False
            publish_relay_status(client)
            print("   ✅ Relé LIGADO (Modo Manual)")
            
        elif payload.upper() == "OFF" or payload == "0" or payload.lower() == "false":
            relay_state = False
            auto_mode = False
            publish_relay_status(client)
            print("   ✅ Relé DESLIGADO (Modo Manual)")
            
        elif payload.upper() == "AUTO":
            auto_mode = True
            print("   ✅ Modo AUTOMÁTICO ativado")

def on_disconnect(client, userdata, reason_code=None, properties=None):
    """Callback quando desconecta do broker"""
    # Compatibilidade com API v1 e v2
    if PAHO_MQTT_V2 and reason_code is not None:
        rc = reason_code.rc if hasattr(reason_code, 'rc') else reason_code
    else:
        rc = reason_code if isinstance(reason_code, int) else 0
    print("\n🔌 Desconectado do broker MQTT")

# ==================== FUNÇÕES DE PUBLICAÇÃO ====================

def publish_temperature(client, temperature):
    """Publica temperatura"""
    temp_str = f"{temperature:.2f}"
    result = client.publish(TOPIC_TEMPERATURE, temp_str, qos=1, retain=True)
    if result.rc == 0:
        print(f"📤 Temperatura: {temperature:.1f} °C")
    return result.rc == 0

def publish_humidity(client, humidity):
    """Publica umidade do ar"""
    hum_str = f"{humidity:.2f}"
    result = client.publish(TOPIC_HUMIDITY, hum_str, qos=1, retain=True)
    if result.rc == 0:
        print(f"📤 Umidade do ar: {humidity:.1f} %")
    return result.rc == 0

def publish_soil_moisture(client, moisture):
    """Publica umidade do solo"""
    soil_str = str(moisture)
    result = client.publish(TOPIC_SOIL_MOISTURE, soil_str, qos=1, retain=True)
    if result.rc == 0:
        print(f"📤 Umidade do solo: {moisture} %")
    return result.rc == 0

def publish_relay_status(client):
    """Publica status do relé"""
    status = "ON" if relay_state else "OFF"
    result = client.publish(TOPIC_RELAY_STATUS, status, qos=1, retain=True)
    if result.rc == 0:
        print(f"📤 Status do relé: {status}")
    return result.rc == 0

def publish_status(client, status):
    """Publica status do sensor"""
    result = client.publish(TOPIC_STATUS, status, qos=1, retain=True)
    return result.rc == 0

# ==================== FUNÇÕES DE SIMULAÇÃO ====================

def simulate_sensors():
    """Simula leitura dos sensores com variação realista"""
    global current_temperature, current_humidity, current_soil_moisture
    
    # Simular temperatura (variação de ±2°C)
    current_temperature += random.uniform(-0.5, 0.5)
    current_temperature = max(20.0, min(30.0, current_temperature))
    
    # Simular umidade do ar (variação de ±3%)
    current_humidity += random.uniform(-1.0, 1.0)
    current_humidity = max(40.0, min(80.0, current_humidity))
    
    # Simular umidade do solo
    if relay_state:
        # Se relé ligado, umidade aumenta
        current_soil_moisture += random.uniform(1.0, 3.0)
    else:
        # Se relé desligado, umidade diminui lentamente
        current_soil_moisture -= random.uniform(0.2, 0.8)
    
    # Limitar valores
    current_soil_moisture = max(0, min(100, current_soil_moisture))
    
    return current_temperature, current_humidity, int(current_soil_moisture)

def check_auto_control(client):
    """Verifica e controla relé automaticamente"""
    global relay_state
    
    if auto_mode:
        if current_soil_moisture < SOIL_MOISTURE_THRESHOLD_LOW and not relay_state:
            relay_state = True
            publish_relay_status(client)
            print("💧 Solo seco detectado! Ligando irrigação...")
        elif current_soil_moisture > SOIL_MOISTURE_THRESHOLD_HIGH and relay_state:
            relay_state = False
            publish_relay_status(client)
            print("✅ Solo úmido suficiente. Desligando irrigação.")

def print_help():
    """Imprime ajuda sobre comandos"""
    print("=" * 50)
    print("COMANDOS DISPONÍVEIS:")
    print("=" * 50)
    print("No terminal, execute:")
    print("")
    print("  # Ligar relé manualmente:")
    print(f"  mosquitto_pub -h {MQTT_BROKER} -t {TOPIC_RELAY_CONTROL} -m ON")
    print("")
    print("  # Desligar relé manualmente:")
    print(f"  mosquitto_pub -h {MQTT_BROKER} -t {TOPIC_RELAY_CONTROL} -m OFF")
    print("")
    print("  # Ativar modo automático:")
    print(f"  mosquitto_pub -h {MQTT_BROKER} -t {TOPIC_RELAY_CONTROL} -m AUTO")
    print("")
    print("  # Monitorar todos os tópicos:")
    print(f"  mosquitto_sub -h {MQTT_BROKER} -t 'sensor/#' -t 'actuator/#' -v")
    print("")
    print("=" * 50)
    print("Pressione Ctrl+C para parar o mock\n")

# ==================== FUNÇÃO PRINCIPAL ====================

def main():
    """Função principal"""
    global relay_state
    
    print("=" * 50)
    print("🤖 Mock ESP32 - Simulador de Sistema de Irrigação")
    print("=" * 50)
    print(f"📡 Conectando ao broker: {MQTT_BROKER}:{MQTT_PORT}...\n")
    
    # Criar cliente MQTT (compatível com paho-mqtt 2.x e 1.x)
    if PAHO_MQTT_V2:
        # Versão 2.x do paho-mqtt - usar VERSION2 (sem depreciação)
        client = mqtt.Client(
            client_id=MQTT_CLIENT_ID,
            callback_api_version=CALLBACK_API_VERSION
        )
    else:
        # Versão 1.x do paho-mqtt
        client = mqtt.Client(MQTT_CLIENT_ID)
    
    client.on_connect = on_connect
    client.on_message = on_message
    client.on_disconnect = on_disconnect
    
    # Conectar ao broker
    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
    except Exception as e:
        print(f"❌ Erro ao conectar ao broker: {e}")
        print(f"   Verifique se o Mosquitto está rodando:")
        print(f"   sudo systemctl status mosquitto")
        sys.exit(1)
    
    # Iniciar loop MQTT em thread separada
    client.loop_start()
    
    # Variáveis de controle de tempo
    last_sensor_publish = 0
    last_status_publish = 0
    
    try:
        while True:
            current_time = time.time()
            
            # Publicar dados dos sensores
            if current_time - last_sensor_publish >= SENSOR_INTERVAL:
                temp, hum, soil = simulate_sensors()
                
                print(f"\n⏰ {datetime.now().strftime('%H:%M:%S')} - Publicando dados:")
                publish_temperature(client, temp)
                publish_humidity(client, hum)
                publish_soil_moisture(client, soil)
                
                # Verificar controle automático
                check_auto_control(client)
                
                last_sensor_publish = current_time
            
            # Publicar status periódico
            if current_time - last_status_publish >= STATUS_INTERVAL:
                publish_status(client, "online")
                publish_relay_status(client)
                last_status_publish = current_time
            
            # Pequeno delay para não sobrecarregar CPU
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        print("\n\n🛑 Parando mock ESP32...")
        publish_status(client, "offline")
        client.loop_stop()
        client.disconnect()
        print("✅ Mock ESP32 finalizado!")
        sys.exit(0)

if __name__ == '__main__':
    main()

