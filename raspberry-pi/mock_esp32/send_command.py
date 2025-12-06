#!/usr/bin/env python3
"""
Script auxiliar para enviar comandos ao mock ESP32
Uso: python3 send_command.py [ON|OFF|AUTO]
"""

import sys
import paho.mqtt.publish as publish

MQTT_BROKER = 'localhost'
TOPIC = 'actuator/relay_control'

def send_command(command):
    """Envia comando para o mock ESP32"""
    try:
        publish.single(TOPIC, command, hostname=MQTT_BROKER, qos=1)
        print(f"✅ Comando '{command}' enviado com sucesso!")
        return True
    except Exception as e:
        print(f"❌ Erro ao enviar comando: {e}")
        return False

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Uso: python3 send_command.py [ON|OFF|AUTO]")
        print("\nExemplos:")
        print("  python3 send_command.py ON    # Liga relé")
        print("  python3 send_command.py OFF   # Desliga relé")
        print("  python3 send_command.py AUTO  # Modo automático")
        sys.exit(1)
    
    command = sys.argv[1].upper()
    
    if command not in ['ON', 'OFF', 'AUTO']:
        print(f"❌ Comando inválido: {command}")
        print("   Use: ON, OFF ou AUTO")
        sys.exit(1)
    
    send_command(command)

