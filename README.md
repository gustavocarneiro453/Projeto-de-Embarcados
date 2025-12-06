# Sistema de Irrigação Automática IoT com ESP32

## 📋 Descrição do Projeto

Sistema IoT de irrigação automática que utiliza módulos ESP32 para monitorar a umidade do solo e controlar automaticamente um sistema de irrigação (bomba/válvula) através de um relé. O sistema também monitora temperatura e umidade do ar através de sensores DHT11, transmitindo todas as informações via protocolo MQTT para um dashboard web em tempo real hospedado em um Raspberry Pi.

### 🎯 Objetivos

- Coletar dados de temperatura, umidade do ar e umidade do solo usando ESP32
- Controlar automaticamente sistema de irrigação baseado na umidade do solo
- Permitir controle manual do relé via dashboard web
- Transmitir dados via Wi-Fi usando protocolo MQTT
- Visualizar dados em tempo real através de dashboard web
- Implementar sistema escalável e modular usando FreeRTOS

### 🏗️ Arquitetura

O sistema utiliza **FreeRTOS** no ESP32 com arquitetura multitarefa:
- **Task WiFiManager**: Gerencia conexão Wi-Fi com reconexão automática
- **Task SensorRead**: Lê sensores periodicamente (temperatura, umidade do ar, umidade do solo)
- **Task RelayControl**: Controla relé automaticamente e processa comandos manuais
- **Task MQTT**: Gerencia comunicação MQTT e publica dados
- **Task StatusPublish**: Publica status do sistema periodicamente

---

## 🔧 Requisitos

### Hardware

- **1x ou 2x módulos ESP32** (NodeMCU ou similar)
- **1x Sensor DHT11** (temperatura e umidade do ar)
- **1x Sensor de Umidade do Solo** (analógico)
- **1x Módulo Relé** (1 canal) para controle da bomba/válvula
- **1x Raspberry Pi** (para broker MQTT e servidor web)
- **Componentes eletrônicos**: resistor 10kΩ, jumpers, protoboard
- **Fonte de alimentação** para ESP32 (USB ou bateria)
- **Bomba de água ou válvula solenoide** (12V ou 24V) + fonte adequada

### Software

#### Raspberry Pi:
- Raspberry Pi OS (Linux) ou Raspbian
- Mosquitto MQTT Broker
- Python 3.x
- Flask (framework web)
- paho-mqtt (biblioteca MQTT Python)

#### ESP32:
- Arduino IDE ou PlatformIO
- Biblioteca PubSubClient (MQTT)
- Biblioteca DHT sensor library (Adafruit)
- Biblioteca Adafruit Unified Sensor
- FreeRTOS (já incluído no ESP32)

#### Windows (para desenvolvimento/testes):
- Python 3.x
- paho-mqtt (para mock ESP32)
- Mosquitto MQTT Broker (opcional, pode usar broker público)

---

## 📁 Estrutura do Repositório

```
.
├── README.md                          # Este arquivo
├── docs/                              # Documentação técnica
│   ├── template_relatorio.tex        # Template relatório ABNT2
│   ├── INSTRUCOES_RELATORIO.md        # Como gerar PDF
│   └── imagens/                       # Imagens para relatório
├── raspberry-pi/                      # Códigos do broker + dashboard
│   ├── broker/
│   │   └── mosquitto.conf             # Configuração do broker MQTT
│   ├── dashboard/
│   │   ├── app.py                     # Aplicação Flask
│   │   ├── requirements.txt           # Dependências Python
│   │   └── templates/
│   │       └── index.html             # Dashboard web
│   ├── mock_esp32/                    # Simulador ESP32 (para testes)
│   │   ├── mock_esp32.py              # Mock principal
│   │   ├── send_command.py            # Script para enviar comandos
│   │   └── requirements.txt           # Dependências
│   └── install.sh                     # Script de instalação
├── esp32-esp8266/                     # Firmware dos módulos
│   └── estacao_meteorologica/
│       └── estacao_meteorologica.ino  # Firmware ESP32 (FreeRTOS)
└── schematics/                         # Diagramas eletrônicos
    ├── circuito_completo.txt           # Diagrama detalhado
    └── diagrama_sistema.txt           # Diagrama de blocos
```

---

## 🚀 Instalação e Configuração

### Parte 1: Configuração do Raspberry Pi

#### 1.1. Instalar Mosquitto MQTT Broker

Abra o terminal no Raspberry Pi e execute:

```bash
# Atualizar sistema
sudo apt update
sudo apt upgrade -y

# Instalar Mosquitto
sudo apt install mosquitto mosquitto-clients -y

# Habilitar e iniciar o serviço
sudo systemctl enable mosquitto
sudo systemctl start mosquitto

# Verificar se está rodando
sudo systemctl status mosquitto
```

#### 1.2. Configurar Mosquitto

```bash
# Copiar arquivo de configuração
cd ~/Projeto-de-Sistema-embarcados/raspberry-pi
sudo cp broker/mosquitto.conf /etc/mosquitto/mosquitto.conf

# Reiniciar serviço
sudo systemctl restart mosquitto
```

#### 1.3. Descobrir IP do Raspberry Pi

```bash
hostname -I
```

Anote o IP (exemplo: `192.168.1.100`) - você precisará dele para configurar o ESP32.

#### 1.4. Instalar Dashboard Web

```bash
# Navegar até o diretório do dashboard
cd ~/Projeto-de-Sistema-embarcados/raspberry-pi/dashboard

# Instalar dependências Python
pip3 install -r requirements.txt

# Se pip3 não estiver instalado:
sudo apt install python3-pip -y
```

#### 1.5. Iniciar Dashboard

```bash
cd ~/Projeto-de-Sistema-embarcados/raspberry-pi/dashboard
python3 app.py
```

Você verá:
```
🚀 Iniciando servidor Flask...
📊 Dashboard disponível em: http://localhost:5000
✅ Conectado ao broker MQTT
```

Acesse no navegador: `http://[IP_DO_RASPBERRY_PI]:5000`

---

### Parte 2: Configuração do ESP32

#### 2.1. Instalar Arduino IDE e Configurar ESP32

1. **Baixar Arduino IDE**: https://www.arduino.cc/en/software

2. **Configurar suporte para ESP32**:
   - File > Preferences
   - Em "Additional Boards Manager URLs", adicione:
     ```
     https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json
     ```
   - Tools > Board > Boards Manager
   - Procure "ESP32" e instale "ESP32 by Espressif Systems"

#### 2.2. Instalar Bibliotecas Necessárias

No Arduino IDE:
- Sketch > Include Library > Manage Libraries
- Instale:
  - `PubSubClient` (por Nick O'Leary)
  - `DHT sensor library` (por Adafruit)
  - `Adafruit Unified Sensor`

#### 2.3. Configurar Credenciais no Código

Abra o arquivo:
```
esp32-esp8266/estacao_meteorologica/estacao_meteorologica.ino
```

Edite as seguintes linhas (aproximadamente linhas 27-30):

```cpp
// Configurações Wi-Fi
const char* WIFI_SSID = "NOME_DA_SUA_REDE_WIFI";      // ← Coloque aqui
const char* WIFI_PASSWORD = "SENHA_DA_SUA_REDE";     // ← Coloque aqui

// Configurações MQTT
const char* MQTT_BROKER = "192.168.1.100";            // ← IP do Raspberry Pi
```

#### 2.4. Ajustar Calibração do Sensor (se necessário)

Se o sensor de umidade do solo não estiver lendo corretamente, ajuste a linha ~245:

```cpp
// Ajuste estes valores conforme seu sensor específico
soilMoisturePercent = map(soilSensorValue, 0, 4095, 100, 0);
```

Teste em solo seco e úmido para calibrar.

#### 2.5. Fazer Upload do Código

1. Conecte o ESP32 via USB
2. No Arduino IDE:
   - Tools > Board > ESP32 Arduino > Selecione seu modelo (ex: "NodeMCU-32S")
   - Tools > Port > Selecione a porta COM do ESP32
   - Clique em "Upload" (seta para a direita)
3. Aguarde a compilação e upload

#### 2.6. Abrir Serial Monitor

- Tools > Serial Monitor
- Velocidade: 115200 baud
- Você verá logs como:
  ```
  ✅ Wi-Fi conectado!
  📶 IP: 192.168.1.50
  ✅ Conectado ao broker MQTT!
  📊 Sensores: T=25.3°C H=60.5% Solo=45%
  ```

---

### Parte 3: Conexão do Hardware

#### 3.1. Sensor DHT11

```
ESP32          DHT11
------         ------
3.3V    --->   VCC
GND     --->   GND
GPIO 4  --->   DATA
              (resistor 10kΩ entre DATA e VCC)
```

#### 3.2. Sensor de Umidade do Solo

```
ESP32          Sensor Solo
------         ------------
3.3V    --->   VCC
GND     --->   GND
GPIO 34 --->   A0 (analógico)
```

#### 3.3. Módulo Relé

```
ESP32          Relé
------         ----
GPIO 2  --->   IN (controle)
GND     --->   GND
5V      --->   VCC (se necessário)
              (NO/COM conectados à bomba/válvula)
```

**Nota:** Consulte `schematics/circuito_completo.txt` para diagrama detalhado.

---

### Parte 4: Testando o Sistema

#### 4.1. Verificar Conexão MQTT

No Raspberry Pi, execute:

```bash
mosquitto_sub -h localhost -t "sensor/#" -v
```

Você deve ver mensagens como:
```
sensor/temperature 25.30
sensor/humidity 60.50
sensor/soil_moisture 45
```

#### 4.2. Testar Controle Manual do Relé

No Raspberry Pi:

```bash
# Ligar relé
mosquitto_pub -h localhost -t "actuator/relay_control" -m "ON"

# Desligar relé
mosquitto_pub -h localhost -t "actuator/relay_control" -m "OFF"

# Ativar modo automático
mosquitto_pub -h localhost -t "actuator/relay_control" -m "AUTO"
```

#### 4.3. Acessar Dashboard

1. No navegador, acesse: `http://[IP_DO_RASPBERRY_PI]:5000`
2. Você deve ver:
   - Cards com temperatura, umidade do ar e umidade do solo
   - Painel de controle do relé
   - Gráficos em tempo real

---

## 🧪 Usando o Mock ESP32 (Para Testes sem Hardware)

Se você não tem o hardware ESP32 disponível, pode usar o simulador:

### Instalação (Windows ou Raspberry Pi)

```bash
cd raspberry-pi/mock_esp32
pip3 install -r requirements.txt
```

### Executar Mock

```bash
python3 mock_esp32.py
```

O mock simula o ESP32, publicando dados de sensores e recebendo comandos.

### Enviar Comandos ao Mock

```bash
# Usando Python
python3 send_command.py ON    # Liga relé
python3 send_command.py OFF   # Desliga relé
python3 send_command.py AUTO  # Modo automático

# Ou usando mosquitto_pub
mosquitto_pub -h localhost -t "actuator/relay_control" -m "ON"
```

### Instalar Mosquitto no Windows (se necessário)

**Opção 1: Download Manual**
1. Baixe: https://mosquitto.org/download/
2. Instale e marque "Install as Windows Service"
3. Inicie: `net start mosquitto`

**Opção 2: Usar Broker Público (para testes)**
Edite `mock_esp32.py`:
```python
MQTT_BROKER = 'test.mosquitto.org'  # Broker público
```

---

## 📊 Funcionalidades

### Coleta de Dados
- ✅ Leitura de temperatura e umidade do ar (DHT11)
- ✅ Leitura de umidade do solo (sensor analógico)
- ✅ Publicação via MQTT a cada 5 segundos

### Controle Automático
- ✅ Liga irrigação quando umidade do solo < 30%
- ✅ Desliga quando umidade do solo > 60%
- ✅ Proteção: desliga após 10 segundos máximo

### Controle Manual
- ✅ Botões no dashboard: Ligar / Desligar / Automático
- ✅ Comandos via MQTT
- ✅ Atualização em tempo real

### Dashboard Web
- ✅ Interface responsiva e moderna
- ✅ Gráficos em tempo real (Chart.js)
- ✅ Histórico de dados (últimos 100 pontos)
- ✅ Indicador de status do sensor e relé
- ✅ Atualização automática a cada 2 segundos

### Sistema Robusto
- ✅ Arquitetura FreeRTOS com tasks separadas
- ✅ Reconexão automática Wi-Fi/MQTT
- ✅ Proteção de recursos com mutexes
- ✅ Logs detalhados via Serial Monitor

---

## 🔌 Tópicos MQTT

### Publicação (ESP32 → Broker)
- `sensor/temperature` - Temperatura do ar em Celsius
- `sensor/humidity` - Umidade do ar em %
- `sensor/soil_moisture` - Umidade do solo em % (0-100)
- `actuator/relay_status` - Status do relé ("ON" ou "OFF")
- `sensor/status` - Status do sensor (online/offline)

### Subscrição (Broker → ESP32)
- `actuator/relay_control` - Controle do relé ("ON", "OFF", "AUTO")

---

## ⚙️ Configurações Ajustáveis

### Limites de Umidade (no código ESP32)

```cpp
const int SOIL_MOISTURE_THRESHOLD_LOW = 30;   // Liga irrigação
const int SOIL_MOISTURE_THRESHOLD_HIGH = 60;  // Desliga irrigação
```

### Duração Máxima de Irrigação

```cpp
const unsigned long IRRIGATION_DURATION_MS = 10000;  // 10 segundos
```

### Intervalos de Publicação

```cpp
#define SENSOR_READ_INTERVAL_TICKS    (pdMS_TO_TICKS(5000))   // 5 segundos
#define RELAY_CONTROL_INTERVAL_TICKS  (pdMS_TO_TICKS(2000))   // 2 segundos
#define STATUS_PUBLISH_INTERVAL_TICKS (pdMS_TO_TICKS(30000))  // 30 segundos
```

---

## 🐛 Solução de Problemas

### ESP32 não conecta ao Wi-Fi
- ✅ Verifique SSID e senha no código
- ✅ Verifique se a rede está no alcance
- ✅ Veja os logs no Serial Monitor

### ESP32 não conecta ao MQTT
- ✅ Verifique se o broker está rodando: `sudo systemctl status mosquitto`
- ✅ Verifique o IP do Raspberry Pi
- ✅ Verifique se estão na mesma rede

### Dashboard não mostra dados
- ✅ Verifique se o dashboard está rodando: `python3 app.py`
- ✅ Verifique se o ESP32 está conectado ao MQTT
- ✅ Teste com `mosquitto_sub` para ver se há mensagens

### Sensor de umidade não funciona
- ✅ Verifique conexões (VCC, GND, sinal)
- ✅ Calibre os valores de `map()` no código
- ✅ Teste com multímetro se o sensor está recebendo energia

### Relé não funciona
- ✅ Verifique conexão no GPIO 2
- ✅ Verifique alimentação do módulo relé
- ✅ Verifique se a bomba/válvula está conectada corretamente
- ✅ Teste o relé manualmente com `digitalWrite(RELAY_PIN, HIGH)`

---

## 📝 Uso do Sistema

### Modo Automático (Padrão)
1. Sistema monitora umidade do solo a cada 2 segundos
2. Liga irrigação quando umidade < 30%
3. Desliga quando umidade > 60%
4. Proteção: desliga após 10 segundos máximo

### Modo Manual
1. Use os botões no dashboard:
   - "Ligar Irrigação" - Liga o relé
   - "Desligar Irrigação" - Desliga o relé
   - "Modo Automático" - Volta ao automático

### Monitoramento
- **Serial Monitor (115200 baud)**: Logs detalhados do ESP32
- **Dashboard Web**: Visualização em tempo real
- **MQTT**: Use `mosquitto_sub` para monitorar mensagens

---

## 🔄 Executar Automaticamente no Raspberry Pi

Para iniciar o dashboard automaticamente ao ligar o Pi:

### Criar serviço systemd

Crie o arquivo `/etc/systemd/system/irrigacao-dashboard.service`:

```ini
[Unit]
Description=Dashboard Sistema Irrigacao IoT
After=network.target mosquitto.service

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/Projeto-de-Sistema-embarcados/raspberry-pi/dashboard
ExecStart=/usr/bin/python3 app.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Ative o serviço:

```bash
sudo systemctl enable irrigacao-dashboard.service
sudo systemctl start irrigacao-dashboard.service
```

---

## 📚 Documentação Adicional

- `esp32-esp8266/ARQUITETURA_FREERTOS.md` - Documentação da arquitetura FreeRTOS
- `schematics/circuito_completo.txt` - Diagrama detalhado do circuito
- `docs/template_relatorio.tex` - Template do relatório técnico (ABNT2)

---

## 👥 Autores

- [Nome do Grupo]

## 📄 Licença

Este projeto é desenvolvido para fins educacionais.

## 🔗 Links Úteis

- [Documentação ESP32](https://docs.espressif.com/projects/esp-idf/en/latest/esp32/)
- [Documentação MQTT](https://mqtt.org/documentation)
- [Documentação Flask](https://flask.palletsprojects.com/)
- [Tutorial Mosquitto](https://mosquitto.org/documentation/)
- [FreeRTOS Documentation](https://www.freertos.org/Documentation/RTOS_book.html)

---

## 📅 Cronograma

- 04/11: Definição da ideia do projeto ✅
- 18/11: Testes preliminares e prototipação
- 02/12: Validação da aplicação web
- 04/12: Apresentação final
- 09/12: Entrega final de todos os artefatos

---

**Projeto desenvolvido para:** Sistemas Embarcados - Cesar School  
**Versão:** 2.1.0  
**Status:** ✅ Sistema completo e funcional
