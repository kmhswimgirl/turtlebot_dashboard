#include <WiFi.h>
#include <SPIFFS.h>
#include <ESP32WebServer.h>
#include <ArduinoJson.h>
#include <WebSocketsServer.h>
#include <wifi-conn.h>
#include <ESP32Ping.h>
#include <time.h>

// constants
const int num_turtlebots = 32;
unsigned long dnsCheck = 0;
const unsigned long dnsInterval = 60000;
char timeStr[32];

// NTP server setup
const char* ntpServer = "pool.ntp.org";
const long gmtOffset_sec = -4 * 3600; 
const int daylightOffset_sec = 3600;  

// wifi credentials
wifiPass psk;
const char* ssid = psk.network;
const char* password = psk.password;

ESP32WebServer server(80);
WebSocketsServer webSocket = WebSocketsServer(81);

String devices[num_turtlebots][4];

void loadDevicesFromFile() {
  File file = SPIFFS.open("/turtlebots.txt", "r");
  if (!file) {
    Serial.println("failed to open turtlebots.txt");
    return;
  }
  int i = 0;
  while (file.available() && i < num_turtlebots) {
    String line = file.readStringUntil('\n');
    line.trim();
    if (line.length() == 0) continue;
    int idx1 = line.indexOf(',');
    int idx2 = line.indexOf(',', idx1 + 1);
    int idx3 = line.indexOf(',', idx2 + 1);
    if (idx1 == -1 || idx2 == -1 || idx3 == -1) continue;
    devices[i][0] = line.substring(0, idx1);
    devices[i][1] = line.substring(idx1 + 1, idx2);
    devices[i][2] = line.substring(idx2 + 1, idx3);
    devices[i][3] = line.substring(idx3 + 1);
    i++;
  }
  file.close();
}

void handletbUpdate() {
  if (server.method() == HTTP_POST) {
    JsonDocument doc;
    DeserializationError error = deserializeJson(doc, server.arg("plain"));
    if (error) {
      server.send(400, "text/plain", "Invalid JSON");
      return;
    }
    String name = doc["name"];
    bool updated = false;
    for (int i = 0; i < num_turtlebots; i++) {
      if (devices[i][0] == name) { // only update column if present in JSON
        if (!doc["ip"].isNull()) devices[i][1] = doc["ip"].as<String>();
        if (!doc["dns"].isNull()) devices[i][2] = doc["dns"].as<String>();

        struct tm timeinfo;
        if (getLocalTime(&timeinfo)) {
          strftime(timeStr, sizeof(timeStr), "%Y-%m-%d %H:%M:%S", &timeinfo);
          devices[i][3] = String(timeStr);
        }

        updated = true;
        break;
      }
    }
    if (updated) {
      server.send(200, "application/json", "{\"status\":\"success\",\"message\":\"Device updated successfully\"}");
      webSocket.broadcastTXT("update");
    } else {
      server.send(404, "application/json", "{\"status\":\"error\",\"message\":\"Device not found\"}");
    }
  } else {
    server.send(405, "text/plain", "Method Not Allowed");
  }
}

void handleGetDevices() {
  JsonDocument doc;
  JsonArray arr = doc.to<JsonArray>();
  for (int i = 0; i < num_turtlebots; i++) {
    JsonObject obj = arr.add<JsonObject>();
    obj["name"] = devices[i][0];
    obj["ip"] = devices[i][1];
    obj["dns"] = devices[i][2];
    obj["lastConnected"] = devices[i][3];
  }
  String output;
  serializeJson(doc, output);
  server.send(200, "application/json", output);
}

void checkAllTurtlebotDNS() {
  for (int i = 0; i < num_turtlebots; i++) {
    String name = devices[i][0];
    if (name.length() > 0) {
      String domain = name + ".dyn.wpi.edu";
      if (Ping.ping(domain.c_str())) {
        devices[i][2] = "Y";
      } else {
        devices[i][2] = "N";
      }
    } else {
      devices[i][2] = "N";
    }
  }
}

void setup() {
  Serial.begin(115200);
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.println("Connecting to WiFi...");
  }
  Serial.println("Connected to WiFi!");

  // NTP server config
  setenv("TZ", "America/New_York", 1); // this doesnt work, had to use offset :(
  tzset();
  configTime(gmtOffset_sec, 0, ntpServer);

  if (!SPIFFS.begin(true)) {
    Serial.println("SPIFFS mount failed");
    return;
  }
  loadDevicesFromFile();

  server.on("/", HTTP_GET, []() {
    File file = SPIFFS.open("/index.html", "r");
    if (!file) {
      server.send(500, "text/plain", "failed to open index.html");
      return;
    }
    server.streamFile(file, "text/html");
    file.close();
  });
  server.on("/tbUpdate", HTTP_POST, handletbUpdate);
  server.on("/devices", HTTP_GET, handleGetDevices);

  // general server for static files
  server.onNotFound([]() {
    String path = server.uri();
    String contentType = "text/plain";
    if (path == "/") {
      path = "/index.html";
      contentType = "text/html";
    } else if (path.endsWith(".css")) {
      contentType = "text/css";
    } else if (path.endsWith(".js")) {
      contentType = "application/javascript";
    } else if (path.endsWith(".html")) {
      contentType = "text/html";
    }
    File file = SPIFFS.open(path, "r");
    if (!file) {
      server.send(404, "text/plain", "File Not Found");
      return;
    }
    server.streamFile(file, contentType);
    file.close();
  });

  server.begin();
  webSocket.begin();

  // check all DNS upon starting or rebooting
  checkAllTurtlebotDNS();
}

void loop() {
  server.handleClient();
  webSocket.loop();

  // dns loop
  if (millis() - dnsCheck > dnsInterval) {
    checkAllTurtlebotDNS();
    dnsCheck = millis();
    webSocket.broadcastTXT("update"); // update clients
  }
}