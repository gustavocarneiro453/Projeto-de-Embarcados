/*
 * Sistema de Irrigação Automática IoT com ESP32
 * Sistema Embarcados - Projeto Final
 * 
 * Este código implementa um sistema de controle de irrigação automática
 * baseado na umidade do solo, com sensor DHT11 e controle de relé
 * que transmite dados via MQTT para um broker no Raspberry Pi
 * 
 * Arquitetura FreeRTOS:
 * - Task de leitura de sensores
 * - Task de controle do relé
 * - Task de comunicação MQTT
 * - Task de publicação de status
 */

#include <WiFi.h>
#include <PubSubClient.h>
#include <DHT.h>
#include <freertos/FreeRTOS.h>
#include <freertos/task.h>
#include <freertos/queue.h>
#include <freertos/semphr.h>

// ==================== CONFIGURAÇÕES ====================

// Configurações Wi-Fi
const char* WIFI_SSID = "SEU_WIFI_SSID";           // Nome da sua rede Wi-Fi
const char* WIFI_PASSWORD = "SUA_SENHA_WIFI";      // Senha da sua rede Wi-Fi

// Configurações MQTT
const char* MQTT_BROKER = "192.168.1.100";         // IP do Raspberry Pi
const int MQTT_PORT = 1883;
const char* MQTT_CLIENT_ID = "ESP32_Irrigacao_01";

// Tópicos MQTT
const char* TOPIC_TEMPERATURE = "sensor/temperature";
const char* TOPIC_HUMIDITY = "sensor/humidity";
const char* TOPIC_SOIL_MOISTURE = "sensor/soil_moisture";
const char* TOPIC_RELAY_STATUS = "actuator/relay_status";
const char* TOPIC_RELAY_CONTROL = "actuator/relay_control";
const char* TOPIC_STATUS = "sensor/status";

// Configurações do Sensor DHT11 (temperatura e umidade do ar)
#define DHTPIN 4              // GPIO 4 conectado ao DATA do DHT11
#define DHTTYPE DHT11         // Tipo do sensor (DHT11 ou DHT22)

// Configurações do Sensor de Umidade do Solo
#define SOIL_SENSOR_PIN 34    // GPIO 34 (ADC1_CH6) - Sensor analógico de umidade do solo

// Configurações do Relé
#define RELAY_PIN 2           // GPIO 2 conectado ao relé (controla bomba/válvula)

// Configurações de Controle Automático
const int SOIL_MOISTURE_THRESHOLD_LOW = 30;   // Umidade mínima (% - liga irrigação)
const int SOIL_MOISTURE_THRESHOLD_HIGH = 60;  // Umidade máxima (% - desliga irrigação)
const unsigned long IRRIGATION_DURATION_MS = 10000;  // Duração máxima de irrigação (10 segundos)

// Configurações FreeRTOS - Intervalos (em ticks)
#define SENSOR_READ_INTERVAL_TICKS    (pdMS_TO_TICKS(5000))   // 5 segundos
#define RELAY_CONTROL_INTERVAL_TICKS  (pdMS_TO_TICKS(2000))   // 2 segundos
#define STATUS_PUBLISH_INTERVAL_TICKS (pdMS_TO_TICKS(30000))  // 30 segundos
#define MQTT_LOOP_INTERVAL_TICKS      (pdMS_TO_TICKS(100))    // 100ms

// Prioridades das Tasks (maior número = maior prioridade)
#define TASK_PRIORITY_HIGH    3
#define TASK_PRIORITY_MEDIUM  2
#define TASK_PRIORITY_LOW     1

// Tamanhos das filas
#define QUEUE_SIZE 10

// ==================== ESTRUTURAS DE DADOS ====================

// Estrutura para dados dos sensores
struct SensorData {
  float temperature;
  float humidity;
  int soilMoisture;
  bool valid;
};

// Estrutura para comandos do relé
struct RelayCommand {
  enum { ON, OFF, AUTO } action;
};

// ==================== OBJETOS ====================

WiFiClient espClient;
PubSubClient mqttClient(espClient);
DHT dht(DHTPIN, DHTTYPE);

// ==================== RECURSOS FreeRTOS ====================

// Filas
QueueHandle_t sensorDataQueue;      // Fila para dados dos sensores
QueueHandle_t relayCommandQueue;     // Fila para comandos do relé
QueueHandle_t mqttPublishQueue;      // Fila para publicações MQTT

// Semáforos/Mutex
SemaphoreHandle_t mqttMutex;        // Mutex para acesso ao cliente MQTT
SemaphoreHandle_t relayMutex;        // Mutex para controle do relé
SemaphoreHandle_t wifiMutex;        // Mutex para acesso Wi-Fi

// Handles das Tasks
TaskHandle_t taskSensorHandle = NULL;
TaskHandle_t taskRelayControlHandle = NULL;
TaskHandle_t taskMQTTHandle = NULL;
TaskHandle_t taskStatusHandle = NULL;
TaskHandle_t taskWiFiHandle = NULL;

// ==================== VARIÁVEIS COMPARTILHADAS ====================

volatile bool wifiConnected = false;
volatile bool mqttConnected = false;
volatile bool relayState = false;                    // Estado atual do relé
volatile bool autoMode = true;                       // Modo automático
volatile int soilMoisturePercent = 0;                // Umidade do solo
volatile unsigned long relayStartTime = 0;           // Tempo de início da irrigação

// ==================== PROTÓTIPOS DE FUNÇÕES ====================

// Tasks FreeRTOS
void taskSensorRead(void *parameter);
void taskRelayControl(void *parameter);
void taskMQTT(void *parameter);
void taskStatusPublish(void *parameter);
void taskWiFiManager(void *parameter);

// Funções auxiliares
void connectWiFi();
void connectMQTT();
void mqttCallback(char* topic, byte* payload, unsigned int length);
void setRelay(bool state);
void publishMQTTMessage(const char* topic, const char* message);

// ==================== SETUP ====================

void setup() {
  // Inicializar Serial
  Serial.begin(115200);
  delay(1000);
  
  Serial.println("\n\n=================================");
  Serial.println("Sistema de Irrigação Automática IoT");
  Serial.println("ESP32 - FreeRTOS");
  Serial.println("=================================\n");

  // Configurar pinos
  pinMode(RELAY_PIN, OUTPUT);
  digitalWrite(RELAY_PIN, LOW);  // Iniciar com relé desligado
  pinMode(SOIL_SENSOR_PIN, INPUT);
  
  Serial.println("✅ GPIO configurados");
  Serial.println("   - Relé: GPIO " + String(RELAY_PIN));
  Serial.println("   - Sensor Solo: GPIO " + String(SOIL_SENSOR_PIN));

  // Inicializar sensor DHT
  dht.begin();
  Serial.println("✅ Sensor DHT11 inicializado");

  // Criar filas FreeRTOS
  sensorDataQueue = xQueueCreate(QUEUE_SIZE, sizeof(SensorData));
  relayCommandQueue = xQueueCreate(QUEUE_SIZE, sizeof(RelayCommand));
  mqttPublishQueue = xQueueCreate(QUEUE_SIZE, sizeof(char*));

  // Criar mutexes
  mqttMutex = xSemaphoreCreateMutex();
  relayMutex = xSemaphoreCreateMutex();
  wifiMutex = xSemaphoreCreateMutex();

  if (sensorDataQueue == NULL || relayCommandQueue == NULL || 
      mqttMutex == NULL || relayMutex == NULL || wifiMutex == NULL) {
    Serial.println("❌ Erro ao criar recursos FreeRTOS!");
    while(1) delay(1000);  // Travar se não conseguir criar recursos
  }

  Serial.println("✅ Recursos FreeRTOS criados");

  // Configurar cliente MQTT
  mqttClient.setServer(MQTT_BROKER, MQTT_PORT);
  mqttClient.setCallback(mqttCallback);

  // Conectar Wi-Fi (bloqueante no setup)
  connectWiFi();

  // Criar Tasks FreeRTOS
  xTaskCreatePinnedToCore(
    taskWiFiManager,           // Função da task
    "WiFiManager",             // Nome da task
    4096,                      // Stack size
    NULL,                      // Parâmetros
    TASK_PRIORITY_HIGH,        // Prioridade
    &taskWiFiHandle,           // Handle
    1                          // Core (0 ou 1)
  );

  xTaskCreatePinnedToCore(
    taskSensorRead,
    "SensorRead",
    4096,
    NULL,
    TASK_PRIORITY_MEDIUM,
    &taskSensorHandle,
    1
  );

  xTaskCreatePinnedToCore(
    taskRelayControl,
    "RelayControl",
    4096,
    NULL,
    TASK_PRIORITY_HIGH,
    &taskRelayControlHandle,
    1
  );

  xTaskCreatePinnedToCore(
    taskMQTT,
    "MQTT",
    8192,                      // Mais stack para MQTT
    NULL,
    TASK_PRIORITY_MEDIUM,
    &taskMQTTHandle,
    0                          // Core diferente para balancear carga
  );

  xTaskCreatePinnedToCore(
    taskStatusPublish,
    "StatusPublish",
    4096,
    NULL,
    TASK_PRIORITY_LOW,
    &taskStatusHandle,
    1
  );

  Serial.println("✅ Tasks FreeRTOS criadas");
  Serial.println("📊 Modo: " + String(autoMode ? "AUTOMÁTICO" : "MANUAL"));
  Serial.println("💧 Limites: " + String(SOIL_MOISTURE_THRESHOLD_LOW) + "% - " + String(SOIL_MOISTURE_THRESHOLD_HIGH) + "%\n");
  Serial.println("🚀 Sistema iniciado! Tasks rodando...\n");
}

// ==================== LOOP (não usado com FreeRTOS) ====================

void loop() {
  // Com FreeRTOS, o loop() fica vazio
  // Todas as funcionalidades são executadas em tasks
  vTaskDelay(pdMS_TO_TICKS(1000));
}

// ==================== TASK: GERENCIAMENTO Wi-Fi ====================

void taskWiFiManager(void *parameter) {
  TickType_t lastCheckTime = 0;
  const TickType_t checkInterval = pdMS_TO_TICKS(10000);  // Verificar a cada 10 segundos

  for(;;) {
    if (xSemaphoreTake(wifiMutex, portMAX_DELAY)) {
      if (WiFi.status() != WL_CONNECTED) {
        wifiConnected = false;
        Serial.println("📡 Reconectando Wi-Fi...");
        connectWiFi();
      } else if (!wifiConnected) {
        wifiConnected = true;
        Serial.println("✅ Wi-Fi conectado!");
      }
      xSemaphoreGive(wifiMutex);
    }
    
    vTaskDelay(checkInterval);
  }
}

// ==================== TASK: LEITURA DE SENSORES ====================

void taskSensorRead(void *parameter) {
  SensorData sensorData;

  for(;;) {
    // Ler temperatura e umidade do ar (DHT11)
    float temperature = dht.readTemperature();
    float humidity = dht.readHumidity();

    // Ler umidade do solo (sensor analógico)
    int soilSensorValue = analogRead(SOIL_SENSOR_PIN);
    // Converter valor analógico (0-4095) para percentual (0-100%)
    int soilMoisture = map(soilSensorValue, 0, 4095, 100, 0);
    soilMoisture = constrain(soilMoisture, 0, 100);

    // Atualizar variável compartilhada
    soilMoisturePercent = soilMoisture;

    // Preparar estrutura de dados
    sensorData.temperature = temperature;
    sensorData.humidity = humidity;
    sensorData.soilMoisture = soilMoisture;
    sensorData.valid = !isnan(temperature) && !isnan(humidity);

    if (sensorData.valid) {
      // Enviar dados para a fila
      if (xQueueSend(sensorDataQueue, &sensorData, 0) != pdTRUE) {
        Serial.println("⚠️ Fila de sensores cheia!");
      } else {
        Serial.print("📊 Sensores: T=");
        Serial.print(temperature, 1);
        Serial.print("°C H=");
        Serial.print(humidity, 1);
        Serial.print("% Solo=");
        Serial.print(soilMoisture);
        Serial.println("%");
      }
    } else {
      Serial.println("⚠️ Erro ao ler dados do sensor DHT11");
    }

    vTaskDelay(SENSOR_READ_INTERVAL_TICKS);
  }
}

// ==================== TASK: CONTROLE DO RELÉ ====================

void taskRelayControl(void *parameter) {
  RelayCommand cmd;
  TickType_t lastCheckTime = 0;

  for(;;) {
    // Verificar comandos na fila (controle manual)
    if (xQueueReceive(relayCommandQueue, &cmd, 0) == pdTRUE) {
      if (xSemaphoreTake(relayMutex, portMAX_DELAY)) {
        switch(cmd.action) {
          case RelayCommand::ON:
            setRelay(true);
            autoMode = false;
            Serial.println("🔧 Controle MANUAL: Relé LIGADO");
            break;
          case RelayCommand::OFF:
            setRelay(false);
            autoMode = false;
            Serial.println("🔧 Controle MANUAL: Relé DESLIGADO");
            break;
          case RelayCommand::AUTO:
            autoMode = true;
            Serial.println("🔧 Modo AUTOMÁTICO ativado");
            break;
        }
        xSemaphoreGive(relayMutex);
      }
    }

    // Controle automático
    if (autoMode) {
      if (xSemaphoreTake(relayMutex, portMAX_DELAY)) {
        // Verificar umidade do solo e controlar relé
        if (soilMoisturePercent < SOIL_MOISTURE_THRESHOLD_LOW && !relayState) {
          setRelay(true);
          Serial.println("💧 Solo seco detectado! Iniciando irrigação...");
        } else if (soilMoisturePercent > SOIL_MOISTURE_THRESHOLD_HIGH && relayState) {
          setRelay(false);
          Serial.println("✅ Solo úmido suficiente. Parando irrigação.");
        }

        // Verificar tempo máximo de irrigação
        if (relayState) {
          unsigned long currentTime = millis();
          if (currentTime - relayStartTime >= IRRIGATION_DURATION_MS) {
            setRelay(false);
            Serial.println("⏱️ Tempo máximo de irrigação atingido. Desligando relé.");
          }
        }

        xSemaphoreGive(relayMutex);
      }
    }

    vTaskDelay(RELAY_CONTROL_INTERVAL_TICKS);
  }
}

// ==================== TASK: COMUNICAÇÃO MQTT ====================

void taskMQTT(void *parameter) {
  SensorData sensorData;
  TickType_t lastReconnectAttempt = 0;
  const TickType_t reconnectInterval = pdMS_TO_TICKS(5000);

  for(;;) {
    // Verificar e reconectar MQTT se necessário
    if (xSemaphoreTake(mqttMutex, portMAX_DELAY)) {
      if (!mqttClient.connected() && wifiConnected) {
        TickType_t currentTime = xTaskGetTickCount();
        if (currentTime - lastReconnectAttempt > reconnectInterval) {
          lastReconnectAttempt = currentTime;
          connectMQTT();
        }
      }

      // Processar loop MQTT
      if (mqttClient.connected()) {
        mqttClient.loop();
        mqttConnected = true;
      } else {
        mqttConnected = false;
      }
      xSemaphoreGive(mqttMutex);
    }

    // Processar dados dos sensores da fila e publicar
    if (xQueueReceive(sensorDataQueue, &sensorData, 0) == pdTRUE) {
      if (sensorData.valid && mqttConnected) {
        if (xSemaphoreTake(mqttMutex, portMAX_DELAY)) {
          // Publicar temperatura
          char tempStr[10];
          dtostrf(sensorData.temperature, 4, 2, tempStr);
          publishMQTTMessage(TOPIC_TEMPERATURE, tempStr);

          // Publicar umidade do ar
          char humStr[10];
          dtostrf(sensorData.humidity, 4, 2, humStr);
          publishMQTTMessage(TOPIC_HUMIDITY, humStr);

          // Publicar umidade do solo
          char soilStr[10];
          itoa(sensorData.soilMoisture, soilStr, 10);
          publishMQTTMessage(TOPIC_SOIL_MOISTURE, soilStr);

          xSemaphoreGive(mqttMutex);
        }
      }
    }

    vTaskDelay(MQTT_LOOP_INTERVAL_TICKS);
  }
}

// ==================== TASK: PUBLICAÇÃO DE STATUS ====================

void taskStatusPublish(void *parameter) {
  for(;;) {
    if (mqttConnected) {
      if (xSemaphoreTake(mqttMutex, portMAX_DELAY)) {
        // Publicar status do sensor
        publishMQTTMessage(TOPIC_STATUS, "online");

        // Publicar status do relé
        const char* relayStatus = relayState ? "ON" : "OFF";
        publishMQTTMessage(TOPIC_RELAY_STATUS, relayStatus);

        xSemaphoreGive(mqttMutex);
      }
    }

    vTaskDelay(STATUS_PUBLISH_INTERVAL_TICKS);
  }
}

// ==================== FUNÇÕES AUXILIARES ====================

void connectWiFi() {
  Serial.print("📡 Conectando ao Wi-Fi: ");
  Serial.println(WIFI_SSID);

  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 20) {
    vTaskDelay(pdMS_TO_TICKS(500));
    Serial.print(".");
    attempts++;
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\n✅ Wi-Fi conectado!");
    Serial.print("📶 IP: ");
    Serial.println(WiFi.localIP());
    Serial.print("📶 RSSI: ");
    Serial.print(WiFi.RSSI());
    Serial.println(" dBm");
    wifiConnected = true;
  } else {
    Serial.println("\n❌ Falha ao conectar ao Wi-Fi");
    wifiConnected = false;
  }
}

void connectMQTT() {
  Serial.print("🔌 Conectando ao broker MQTT: ");
  Serial.print(MQTT_BROKER);
  Serial.print(":");
  Serial.println(MQTT_PORT);

  if (mqttClient.connect(MQTT_CLIENT_ID)) {
    Serial.println("✅ Conectado ao broker MQTT!");
    // Subscrever ao tópico de controle do relé
    mqttClient.subscribe(TOPIC_RELAY_CONTROL);
    Serial.println("📡 Inscrito no tópico de controle: " + String(TOPIC_RELAY_CONTROL));
    publishMQTTMessage(TOPIC_STATUS, "online");
    
    const char* relayStatus = relayState ? "ON" : "OFF";
    publishMQTTMessage(TOPIC_RELAY_STATUS, relayStatus);
  } else {
    Serial.print("❌ Falha na conexão MQTT. Código: ");
    Serial.println(mqttClient.state());
  }
}

void mqttCallback(char* topic, byte* payload, unsigned int length) {
  // Callback para mensagens recebidas (controle do relé)
  String message = "";
  for (int i = 0; i < length; i++) {
    message += (char)payload[i];
  }
  
  Serial.print("📨 Mensagem recebida: ");
  Serial.print(topic);
  Serial.print(" -> ");
  Serial.println(message);

  // Processar comando de controle do relé
  if (String(topic) == TOPIC_RELAY_CONTROL) {
    RelayCommand cmd;
    
    if (message == "ON" || message == "1" || message == "true") {
      cmd.action = RelayCommand::ON;
    } else if (message == "OFF" || message == "0" || message == "false") {
      cmd.action = RelayCommand::OFF;
    } else if (message == "AUTO") {
      cmd.action = RelayCommand::AUTO;
    } else {
      return;  // Comando inválido
    }

    // Enviar comando para a fila
    if (xQueueSend(relayCommandQueue, &cmd, 0) != pdTRUE) {
      Serial.println("⚠️ Fila de comandos do relé cheia!");
    }
  }
}

void setRelay(bool state) {
  relayState = state;
  digitalWrite(RELAY_PIN, state ? HIGH : LOW);
  
  if (state) {
    relayStartTime = millis();  // Registrar início da irrigação
  }
  
  Serial.print("🔌 Relé: ");
  Serial.println(state ? "LIGADO" : "DESLIGADO");
}

void publishMQTTMessage(const char* topic, const char* message) {
  if (mqttClient.connected()) {
    mqttClient.publish(topic, message, true);
  }
}
