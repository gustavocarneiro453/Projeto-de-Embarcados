#!/bin/bash
# Script de teste para enviar comandos ao mock ESP32
# Uso: ./test_commands.sh

BROKER="localhost"
TOPIC="actuator/relay_control"

echo "=========================================="
echo "Teste de Comandos - Mock ESP32"
echo "=========================================="
echo ""

echo "1. Ligando relé..."
mosquitto_pub -h $BROKER -t $TOPIC -m "ON"
sleep 2

echo ""
echo "2. Desligando relé..."
mosquitto_pub -h $BROKER -t $TOPIC -m "OFF"
sleep 2

echo ""
echo "3. Ativando modo automático..."
mosquitto_pub -h $BROKER -t $TOPIC -m "AUTO"
sleep 2

echo ""
echo "✅ Testes concluídos!"
echo ""
echo "Para monitorar as mensagens, execute em outro terminal:"
echo "  mosquitto_sub -h localhost -t 'sensor/#' -t 'actuator/#' -v"

