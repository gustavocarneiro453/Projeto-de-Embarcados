#!/bin/bash
# Script de instalação automatizada para Raspberry Pi
# Execute: chmod +x install.sh && ./install.sh

echo "=========================================="
echo "Instalação do Sistema IoT - Estação Meteorológica"
echo "=========================================="
echo ""

# Atualizar sistema
echo "📦 Atualizando sistema..."
sudo apt update
sudo apt upgrade -y

# Instalar Mosquitto MQTT Broker
echo ""
echo "📡 Instalando Mosquitto MQTT Broker..."
sudo apt install mosquitto mosquitto-clients -y

# Configurar Mosquitto
echo ""
echo "⚙️ Configurando Mosquitto..."
sudo cp broker/mosquitto.conf /etc/mosquitto/mosquitto.conf
sudo systemctl enable mosquitto
sudo systemctl restart mosquitto

# Verificar status do Mosquitto
echo ""
echo "✅ Verificando status do Mosquitto..."
sudo systemctl status mosquitto --no-pager -l

# Instalar Python e pip
echo ""
echo "🐍 Instalando Python e pip..."
sudo apt install python3 python3-pip -y

# Instalar dependências do dashboard
echo ""
echo "📊 Instalando dependências do dashboard..."
cd dashboard
pip3 install -r requirements.txt

echo ""
echo "=========================================="
echo "✅ Instalação concluída!"
echo "=========================================="
echo ""
echo "Para iniciar o dashboard, execute:"
echo "  cd raspberry-pi/dashboard"
echo "  python3 app.py"
echo ""
echo "O dashboard estará disponível em: http://localhost:5000"
echo ""

