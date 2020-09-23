#include <Wire.h>
#include "RTClib.h"

RTC_DS1307 RTC;

//#include <timestamp32bits.h>

//#include <ArduinoBearSSL.h>
#include <ESP8266WiFi.h>
#include <WiFiClientSecure.h>
#include <MQTT.h>
#include <ArduinoJson.h>
#include <time.h>
#define emptyString String()

//tmElements_t tm;

// NodeMCU sensor pin definition
#define LIGHTSENSOR1 A0 

// Error handling functions
#include "errors.h"

// Configuration data
#include "configuration.h"

// Define MQTT port
const int MQTT_PORT = 8883;

// Define subscription and publication topics (on thing shadow)
const char MQTT_SUB_TOPIC[] = "$aws/things/1-1/shadow/update";
const char MQTT_PUB_TOPIC[] = "event/test";

// Enable or disable summer­time
#ifdef USE_SUMMER_TIME_DST
uint8_t DST = 1;
#else
uint8_t DST = 0;
#endif
// Create Transport Layer Security (TLS) connection
WiFiClientSecure net;
// Load certificates
BearSSL::X509List cert(cacert);
BearSSL::X509List client_crt(client_cert);
BearSSL::PrivateKey key(privkey);
// Initialize MQTT client
MQTTClient client;  
unsigned long lastMs = 0;
unsigned long previousmillis = 0;
long delta = 0;
time_t now;
time_t nowish = 1510592825;

/* 
  0: status board
    0 => free
    1 => not free
  1: id event
  2: title event
  3: start_time
  4: end_time
*/
//char board[5] = ["free", null, null, null, null];

bool status_board = false;
int id_event_board = 0;
String title_event_board = "";
String st_event_board = "";
String en_event_board = "";

struct tm timeinfo;
bool nextEvent;
int st_h, st_m, st_s, et_h, et_m, et_s;

// Get time through Simple Network Time Protocol 
void NTPConnect(void)
{
  Serial.print("Setting time using SNTP");
  configTime(TIME_ZONE * 3600, DST * 3600, "pool.ntp.org", "time.nist.gov");
  now = time(nullptr);
  Serial.println("ciaooo");
  while (now < nowish)
  {
    delay(500);
    Serial.print("+");
    now = time(nullptr);
  }
  Serial.println("done!");
  //struct tm timeinfo;
  gmtime_r(&now, &timeinfo);
  Serial.print("Current time: ");
  String tmp = asctime(&timeinfo);
  Serial.println(tmp);
  int ora = timeinfo.tm_hour;
  Serial.println (ora);

  RTC.adjust(DateTime(now));  
}

bool getTime(const char *str, String value)
{
  int Hour, Min, Sec;
  
  if (value == "start_time"){
    if (sscanf(str, "%d:%d:%d", &Hour, &Min, &Sec) != 3) return false;
    st_h = Hour;
    st_m = Min;
    st_s = Sec;
    Serial.println("Ora start:");
    Serial.print(st_h);
    return true;
  } else {
    if (sscanf(str, "%d:%d:%d", &Hour, &Min, &Sec) != 3) return false;
    et_h = Hour;
    et_m = Min;
    et_s = Sec;
    return true;
  }
 
}

long checkDeltaTimeEvent (int h1, int m1, int s1, int h2, int m2, int s2) {
  int hourF, minuteF, secondF, result;

  hourF = h1 - h2;
  minuteF = m1 - m2;
  secondF = s1 - s2;

  return ((hourF*3600)+(minuteF*60)+secondF)*1000;
  }

// MQTT management of incoming messages
void checkRoom_NewEvent() {
  
  if(status_board == false) {
    Serial.println("Sto settando il delta");

    delta = checkDeltaTimeEvent(st_h, st_m, st_s, timeinfo.tm_hour, timeinfo.tm_min, timeinfo.tm_sec);
    Serial.println("Valore delta");
    Serial.print(delta);
  }
  
}

void messageReceived(MQTTClient *client, char topic[], char payload[], int payload_length)
{
  StaticJsonDocument<200> doc;
  deserializeJson(doc, payload);
  const int id1 = doc["id"];
  const char* title1 = doc["title"];
  const char* start_time = doc["start_time"];
  const char* end_time = doc["end_time"];

  //Serial.println(id1);

  int id =  id1;
  String title = String (title1);
  //String start_time = String (start_time1);
  //DateTime start_time = new DateTime (NULL, start_time1);
  //DateTime end_time = new DateTime (NULL, end_time1);

  Serial.println("Lunghezza:");
  Serial.println(payload_length);
  if (payload_length != 2){
    Serial.println("Id board:");
    Serial.print(id_event_board);
    Serial.println("Id nuovo evento");
    Serial.print(id);
    Serial.println("Status board");
    Serial.print(status_board);
    
    if (id_event_board != id && status_board == false) {
        NTPConnect();
        getTime(start_time, "start_time");
        getTime(end_time, "end_time");
        checkRoom_NewEvent();
        nextEvent = true;
        id_event_board = id;
      } else if(status_board == true) {
           //Se arriva un evento mentre l'aula è prenotata, risetto solo queste varibili
           getTime(start_time, "start_time");
           getTime(end_time, "end_time"); 
        }
    
  }

  //Serial.println(start_time.substring(1,2));
  //Data start_time = createData(start_time1);
  //Data end_time = createData(end_time1);
  //checkRoom(id, title, start_time, end_time);
}

void busyRoom(bool value) {

  if(value == true) {
    //delta calcolato tra start_time e end_time dell'evento in corso
    delta = checkDeltaTimeEvent(et_h, et_m, et_s, st_h, st_m, st_s);
  } else {
    delta = 0;
    }
  
  status_board = value;
    //title_event_board = "";
    //st_event_board = ;
    //en_event_board = "";

    //onLed()

    Serial.println("stato aula cambiato");
  
}


/*
void messageReceived(String &topic, String &payload)
{
  Serial.println("Received [" + topic + "]: " + payload);
}
*/
/*
void checkRoom(int id, String title, DateTime start_time, DateTime end_time){
  
  
}
*/
// MQTT Broker connection
void connectToMqtt(bool nonBlocking = false)
{
  Serial.println("MQTT connecting ");
  while (!client.connected())
  {
    if (client.connect(THINGNAME))
    { Serial.println("connected!");
      if (!client.subscribe(MQTT_SUB_TOPIC))
        Serial.println("TEST!");
        lwMQTTErr(client.lastError()); }
    else
    { Serial.print("SSL Error Code: ");
      Serial.println(net.getLastSSLError());
      Serial.print("failed, reason ­> ");
      lwMQTTErrConnection(client.returnCode());
      if (!nonBlocking) {
        Serial.println(" < try again in 5 seconds");
        delay(5000);
      }
      else { Serial.println(" <"); }
    }
    if (nonBlocking) break;
  }
}

// Wi­Fi connection
void connectToWiFi(String init_str)
{
  if (init_str != emptyString)
    Serial.print(init_str);
  while (WiFi.status() != WL_CONNECTED)
  {
    Serial.print(".");
    delay(1000);
  }
  if (init_str != emptyString)
    Serial.println("ok!");
}
void verifyWiFiAndMQTT(void)
{
  connectToWiFi("Checking WiFi");
  connectToMqtt();
}
unsigned long previousMillis = 0;
const long interval = 5000;

// MQTT management of outgoing messages
void sendData(void)
{
  DynamicJsonDocument jsonBuffer(JSON_OBJECT_SIZE(3) + 100);
  JsonObject root = jsonBuffer.to<JsonObject>();
  //JsonObject key = root.createNestedObject("key");
  //JsonObject state_reported = state.createNestedObject("reported");
  
  //int value1 = analogRead(LIGHTSENSOR1);
  
  root["message"] = "Ciao";
  
  Serial.printf("Sending  [%s]: ", MQTT_PUB_TOPIC);
  serializeJson(root, Serial);
  Serial.println();
  char shadow[measureJson(root) + 1];
  serializeJson(root, shadow, sizeof(shadow));
  if (!client.publish(MQTT_PUB_TOPIC, shadow, false, 0))
    lwMQTTErr(client.lastError());
}

void setup()
{
  Serial.begin(115200);
  delay(5000);
  Serial.println();
  Serial.println();

  WiFi.hostname(THINGNAME);
  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, pass);
  connectToWiFi(String("Trying to connect with SSID: ") + String(ssid));
 
  NTPConnect();
  
  net.setTrustAnchors(&cert);
  net.setClientRSACert(&client_crt, &key);
  client.begin(MQTT_HOST, MQTT_PORT, net);
  
  //client.onMessageAdvanced(messageReceived);
  
  connectToMqtt();
  sendData();
}

void loop()
{  
  delay(1000);
  
  now = time(nullptr);
  if (!client.connected())
  {
    verifyWiFiAndMQTT();
  }
  else
  {
    client.loop();
    if (millis() - lastMs > 5000)
    { //Controllo status board
      lastMs = millis();

      //checkRoom();
      
      //sendData();
    }
  }

   unsigned long currentmillis = millis();
  // questo if serve per prenotare l'aula quando è trascorso delta tempo
  if (((currentmillis - previousmillis >= delta) && status_board == false) && nextEvent == true) {
    previousmillis = currentmillis; 
    busyRoom(true);
    Serial.println("Evento programmato: stanza occupata");
    }

  // questo if serve per liberare l'aula quando è trascorso delta tempo
  if ((currentmillis - previousmillis >= delta) && status_board == true) {
    previousmillis = currentmillis; 
    busyRoom(false);
    nextEvent = false;
    Serial.println("senza liberata");
    }
}
