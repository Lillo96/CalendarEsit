#include <Wire.h>
#include "RTClib.h"

RTC_DS1307 RTC;

#include <LiquidCrystal_I2C.h>

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
const char MQTT_SUB_TOPIC[] = "$aws/things/3-3/shadow/update";
const char MQTT_PUB_TOPIC[] = "event/new";
const char MQTT_PUB1_TOPIC[] = "event/update";

#define CALENDAR_ID 3;
#define GROUP_ID 3;

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
unsigned long pmillis = 0;
long delta = 0;
time_t now;
time_t nowish = 1510592825;

// set the LCD number of columns and rows
int lcdColumns = 16;
int lcdRows = 2;

int ledpin1 = D0; //D0(gpio16)
int ledpin2 = D3; //D3(gpio0)
int button = D5; //D5(gpio14)
int buttonState = 0;

// set LCD address, number of columns and rows
// if you don't know your display address, run an I2C scanner sketch
LiquidCrystal_I2C lcd(0x27, lcdColumns, lcdRows);  

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

// setto i led e lcd nel caso in cui l'aula sia libera
void setLCDandLed_stanzaLibera(){
    // clears the display to print new message
    lcd.clear();
    digitalWrite(ledpin1, LOW);
    digitalWrite(ledpin2, HIGH);

    // set cursor to first column, first row
    lcd.setCursor(0, 0);
    // print message
    lcd.print("Stanza libera");

    // set cursor to second colum, second row
    lcd.setCursor(0, 1);
    // print message
    lcd.print("");

    delay(1000); //IMPORTANTE
    //myDelay(1000);
}

// setto i led e lcd nel caso in cui l'aula sia occupata
void setLCDandLed_stanzaOccupata(){
    digitalWrite(ledpin1, HIGH); 
    digitalWrite(ledpin2, LOW);

    // clears the display to print new message
    lcd.clear();
    
    delay(200);
    //myDelay(200);
    // set cursor to first column, first row
    lcd.setCursor(0, 0);
    // print message
    lcd.print(title_event_board);

    // set cursor to second colum, second row
    lcd.setCursor(0, 1);
    // print message
    lcd.print(st_h + String(":") + st_m + ":" + st_s + "-" + et_h + ":" + et_m + ":" + et_s);
    
    delay(1000); //IMPORTANTE
    //myDelay(1000);
    // clears the display to print new message
}

// Get time through Simple Network Time Protocol 
void NTPConnect(void)
{
  Serial.print("Setting time using SNTP");
  configTime(TIME_ZONE * 3600, DST * 3600, "pool.ntp.org", "time.nist.gov");
  now = time(nullptr);
  while (now < nowish)
  {
    delay(500);
    //myDelay(500);
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
 
  Serial.println("Lunghezza:");
  Serial.println(payload_length);

  // non è un []
  if (payload_length != 2){
    Serial.println("Id board:");
    Serial.print(id_event_board);
    Serial.println("Id nuovo evento");
    Serial.print(id);
    Serial.println("Status board");
    Serial.print(status_board);

    // caso in cui l'aula sia libera
    if (id_event_board != id && status_board == false) {
        Serial.println("AULA LIBERA");
        NTPConnect();
        getTime(start_time, "start_time");
        getTime(end_time, "end_time");
        title_event_board = title;
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
     
    setLCDandLed_stanzaOccupata();
  } else {
     delta = 0;
     setLCDandLed_stanzaLibera();
    }
  
  status_board = value;
 
  Serial.println("stato aula cambiato");  
}

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
        //myDelay(5000);
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
    //myDelay(1000);
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
void sendData(int value)
{
  DynamicJsonDocument jsonBuffer(JSON_OBJECT_SIZE(3) + 100);
  JsonObject root = jsonBuffer.to<JsonObject>();
  //JsonObject key = root.createNestedObject("key");
  //JsonObject state_reported = state.createNestedObject("reported");
  
  //int value1 = analogRead(LIGHTSENSOR1);

  root["group_id"] = GROUP_ID;
  root["calendar_id"] = CALENDAR_ID;

  serializeJson(root, Serial);
  Serial.println();
  char shadow[measureJson(root) + 1];
  serializeJson(root, shadow, sizeof(shadow));
    
  //Serial.printf("Sending  [%s]: ", topic);

  //Con value a 0 è per aggiungere un nuovo evento 
  if (value == 0) {
    if (!client.publish(MQTT_PUB_TOPIC, shadow, false, 0))
      lwMQTTErr(client.lastError());
    } else {
        //Con value a 1 è per avere il prossimo evento 
        if (!client.publish(MQTT_PUB1_TOPIC, shadow, false, 0))
          lwMQTTErr(client.lastError());
      }
}

void setup()
{
  pinMode(ledpin1, OUTPUT);
  pinMode(ledpin2, OUTPUT);
  pinMode(button, INPUT);

  // initialize LCD
  lcd.init();
  // turn on LCD backlight                      
  lcd.backlight();

  setLCDandLed_stanzaLibera();
  
  Serial.begin(115200);
  delay(1000);
  //myDelay(5000);
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

  connectToMqtt();
  sendData(1); //inizializzo la node appena accesa quindi richiedo se vi o meno un evento
  client.onMessageAdvanced(messageReceived);
  
}

void loop()
{  
  //delay(1000);

  buttonState=digitalRead(button);
  
  now = time(nullptr);
  if (!client.connected())
  {
    verifyWiFiAndMQTT();
  }
  else
  {
    client.loop();
    //if (millis() - lastMs > 5000)
    //{ //Controllo status board
      //lastMs = millis();

      if (buttonState==1){
          Serial.println("Botton ON");
          Serial.println("VALORE DELTA QUANDO BUTTON È 1");
          Serial.println(delta);
          if (status_board == false && (delta >= 3600000 || delta == 0)) {
              Serial.println("Dentro add event con button");
              sendData(0); //aggiungo un nuovo evento se è possibile
            } else {
              Serial.println("Dentro ERRORE add event con button");
                lcd.clear();
               // set cursor to first column, first row
                lcd.setCursor(0, 0);
                // print message
                lcd.print("Errore! Aula");
            
                // set cursor to second colum, second row
                lcd.setCursor(0, 1);
                // print message
                lcd.print("non prenotabile");

                delay(1000); //IMPORTANTE
                //myDelay(1000);
                if (status_board == true){
                    setLCDandLed_stanzaOccupata();
                  } else {
                      setLCDandLed_stanzaLibera();
                  }
              }
          
          delay(200);
          //myDelay(200);
      

      //checkRoom();
      
      //sendData();
    }
  }

   unsigned long currentmillis = millis();
  // questo if serve per prenotare l'aula quando è trascorso delta tempo
  //Serial.println("VALORE DELTA PRIMA DI PRENOTARE:");
  //Serial.println(delta);
  if ((((currentmillis - pmillis >= delta) && status_board == false) && nextEvent == true) || delta < 0 ){
    Serial.println("Currentmillis in prenotazione aula");
    Serial.println(currentmillis);
    pmillis = currentmillis; 
    busyRoom(true);
    Serial.println("Evento programmato: stanza occupata");
    }

  // questo if serve per liberare l'aula quando è trascorso delta tempo
  if ((currentmillis - pmillis >= delta) && status_board == true) {
     Serial.println("Currentmillis in libera aula");
    Serial.println(currentmillis);
    
    pmillis = currentmillis; 
    busyRoom(false);
    nextEvent = false;
    Serial.println("stanza liberata");
    sendData(1); //l'evento è terminato e aggiorno la board per sapere se vi è un nuovo evento
    }
}
