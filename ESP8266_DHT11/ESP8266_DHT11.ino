#include <ESP8266WiFi.h>
#include <ESP8266HTTPClient.h>
#include <WiFiClient.h>
#include <DHT.h>

#define DHTPIN D4
#define DHTTYPE DHT11

const char* WIFI_SSID = "WIFI_ADI";
const char* WIFI_PASSWORD = "WIFI_SIFRE";
const char* SERVER_URL = "http://192.168.1.10:8000/sensor/update";
const char* DEVICE_KEY = "ESP_DEVICE_KEY";
const char* DEVICE_ID = "esp8266-dht11";
const unsigned long SEND_INTERVAL_MS = 300000;

DHT dht(DHTPIN, DHTTYPE);

void connectWifi() {
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  Serial.print("WiFi baglaniyor");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println();
  Serial.print("Baglandi. IP: ");
  Serial.println(WiFi.localIP());
}

bool sendSensorData(float temperature, float humidity) {
  if (WiFi.status() != WL_CONNECTED) {
    connectWifi();
  }

  WiFiClient client;
  HTTPClient http;
  http.begin(client, SERVER_URL);
  http.addHeader("Content-Type", "application/json");

  String payload = "{";
  payload += "\"device_id\":\"" + String(DEVICE_ID) + "\",";
  payload += "\"temperature\":" + String(temperature, 2) + ",";
  payload += "\"humidity\":" + String(humidity, 2) + ",";
  payload += "\"device_key\":\"" + String(DEVICE_KEY) + "\"";
  payload += "}";

  int httpCode = http.POST(payload);
  String response = http.getString();

  Serial.print("HTTP Kod: ");
  Serial.println(httpCode);
  Serial.print("Cevap: ");
  Serial.println(response);

  http.end();
  return httpCode > 0 && httpCode < 300;
}

void setup() {
  Serial.begin(115200);
  delay(1000);
  dht.begin();
  connectWifi();
}

void loop() {
  float humidity = dht.readHumidity();
  float temperature = dht.readTemperature();

  if (isnan(humidity) || isnan(temperature)) {
    Serial.println("DHT11 okunamadi");
    delay(5000);
    return;
  }

  Serial.print("Sicaklik: ");
  Serial.print(temperature);
  Serial.print(" C | Nem: ");
  Serial.print(humidity);
  Serial.println(" %");

  sendSensorData(temperature, humidity);
  delay(SEND_INTERVAL_MS);
}
