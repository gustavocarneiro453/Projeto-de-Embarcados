#!/usr/bin/env python3
"""
Script de teste para verificar o funcionamento do broker MQTT
Execute: python3 test_mqtt.py
"""

import paho.mqtt.client as mqtt
import time
import sys

# Configurações
BROKER = 'localhost'
PORT = 1883
TOPICS = ['sensor/temperature', 'sensor/humidity', 'sensor/status']

def on_connect(client, userdata, flags, rc):
    """Callback quando conecta ao broker"""
    if rc == 0:
        print("✅ Conectado ao broker MQTT com sucesso!")
        print(f"📡 Inscrito nos tópicos: {', '.join(TOPICS)}\n")
        for topic in TOPICS:
            client.subscribe(topic)
    else:
        print(f"❌ Falha na conexão. Código: {rc}")
        sys.exit(1)

def on_message(client, userdata, msg):
    """Callback quando recebe mensagem"""
    print(f"📨 [{msg.topic}] {msg.payload.decode('utf-8')}")

def on_disconnect(client, userdata, rc):
    """Callback quando desconecta"""
    print("\n🔌 Desconectado do broker")

def main():
    print("=" * 50)
    print("Teste do Broker MQTT")
    print("=" * 50)
    print(f"Broker: {BROKER}:{PORT}\n")
    
    # Criar cliente MQTT
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.on_disconnect = on_disconnect
    
    try:
        # Conectar ao broker
        print("🔌 Conectando ao broker...")
        client.connect(BROKER, PORT, 60)
        
        # Iniciar loop
        client.loop_start()
        
        print("⏳ Aguardando mensagens (pressione Ctrl+C para sair)...\n")
        
        # Manter script rodando
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n\n🛑 Interrompendo teste...")
            client.loop_stop()
            client.disconnect()
            print("✅ Teste finalizado")
            
    except ConnectionRefusedError:
        print("❌ Erro: Não foi possível conectar ao broker MQTT")
        print("   Verifique se o Mosquitto está rodando:")
        print("   sudo systemctl status mosquitto")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Erro: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()

