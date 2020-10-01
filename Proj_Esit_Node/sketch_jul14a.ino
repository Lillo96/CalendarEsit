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

/*
 * Varibili globali utili per il messaggi dell'update board e nuova prenotazione
 */

#define CALENDAR_ID 5;
#define GROUP_ID 7;

// Define subscription and publication topics (on thing shadow)

//Topic per la ricezione di un evento o array vuoto []
const char MQTT_SUB_TOPIC[] = "$aws/things/" GROUP_ID_1 "-" CALENDAR_ID_1 "/shadow/update";
//Topic per l'invio di una prenotazione
const char MQTT_PUB_TOPIC[] = "event/new";
//Topic per l'invio di un messaggio per l'aggiornamento della board
const char MQTT_PUB1_TOPIC[] = "event/update";

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
unsigned long pmillis;
unsigned long currentmillis;

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

bool status_board = false;
int id_event_board = 0;
String title_event_board = "";
String st_event_board = "";
String en_event_board = "";

struct tm timeinfo;
bool nextEvent;
int st_h, st_m, st_s, et_h, et_m, et_s;

//Setto i led e LCD nel caso in cui l'aula sia libera
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

//Setto i led e lcd nel caso in cui l'aula sia occupata
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

//Stampo le info del prossimo evento
void setLCDandLed_InfoNextEvent(){
    Serial.println("DENTRO next event");
  
    // clears the display to print new message
    lcd.clear();
    digitalWrite(ledpin1, LOW);
    digitalWrite(ledpin2, HIGH);

    // set cursor to first column, first row
    lcd.setCursor(0, 0);
    // print message
    lcd.print(String("N.E.:") + title_event_board);

    // set cursor to second colum, second row
    lcd.setCursor(0, 1);
    // print message
    lcd.print(st_h + String(":") + st_m + ":" + st_s + "-" + et_h + ":" + et_m + ":" + et_s);

    delay(1000); //IMPORTANTE
    //myDelay(1000);
}

// Get time through Simple Network Time Protocol 
void NTPConnect(void)
{  
  Serial.print("Setting time using SNTP");
  configTime(TIME_ZONE * 3600, DST * 3600, "pool.ntp.org", "time.nist.gov");
  //configTime(0, 0, "pool.ntp.org", "time.nist.gov");
  now = time(nullptr);
  while (now < nowish)
  {
    delay(500);
    //myDelay(500);
    Serial.print("+");
    now = time(nullptr);
  }
  Serial.println("done!");
  gmtime_r(&now, &timeinfo);
  Serial.print("Current time: ");
  String tmp = asctime(&timeinfo);
  Serial.println(tmp);
  int ora = timeinfo.tm_hour;
  Serial.println("Orario attuale:");
  Serial.println (ora);

  RTC.adjust(DateTime(now));  
}

//Funzione per estrarre le ore, minuti e secondi in variabili intere
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

//Funzione per calcolare il delta tra due time differenti
long checkDeltaTimeEvent (int h1, int m1, int s1, int h2, int m2, int s2) {
  int hourF, minuteF, secondF, result;

  Serial.println("DENTRO CHECKDELTATIME");

  hourF = h1 - h2;
  minuteF = m1 - m2;
  secondF = s1 - s2;

  return ((hourF*3600)+(minuteF*60)+secondF)*1000;
  }

//Funzione per settare il valore del delta
void checkRoom_NewEvent() {
  
  if(status_board == false) {
    Serial.println("Sto settando il delta");

    delta = checkDeltaTimeEvent(st_h, st_m, st_s, timeinfo.tm_hour, timeinfo.tm_min, timeinfo.tm_sec);
    Serial.println("Valore delta");
    Serial.print(delta);
    
  }
  
}

//Gestione della ricezione di un nuovo messaggio
void messageReceived(MQTTClient *client, char topic[], char payload[], int payload_length)
{
  //Deserializzazione del messaggio JSON in arrivo
  StaticJsonDocument<200> doc;
  deserializeJson(doc, payload);
  const int id1 = doc["id"];
  const char* title1 = doc["title"];
  const char* start_time = doc["start_time"];
  const char* end_time = doc["end_time"];

  int id =  id1;
  String title = String (title1);
 
  Serial.println("Lunghezza:");
  Serial.println(payload_length);

  /*
   * I messagi che possono essere ricevuti, sono di due tipologie:
   *  - Messaggio contenente le info di un evento (nel caso in cui ci 
   *    sia un evento in corso o prossimo, in data odierna)
   *  - Messaggio contenente un array vuoto [] nel caso in cui non vi sia 
   *    nessuna prenotazione in corso o prossima (in data odierna)   
   */


  // non è un []
  if (payload_length != 2){
    Serial.println("Id board:");
    Serial.print(id_event_board);
    Serial.println("Id nuovo evento");
    Serial.print(id);
    Serial.println("Status board");
    Serial.print(status_board);

    //Caso in cui l'aula sia libera
    if (id_event_board != id && status_board == false) {
        Serial.println("AULA LIBERA");
        NTPConnect();
        getTime(start_time, "start_time");
        getTime(end_time, "end_time");
        title_event_board = title;
        pmillis = currentmillis;
        checkRoom_NewEvent();
        nextEvent = true;
        id_event_board = id;
        //stampa info prossimo evento
        setLCDandLed_InfoNextEvent();
      } else if(status_board == true) {
           //Se arriva un evento mentre l'aula è prenotata, risetto solo queste varibili
           getTime(start_time, "start_time");
           getTime(end_time, "end_time"); 
        }
    
  }

}

//Funzione per occupare/liberare l'aula 
void busyRoom(bool value) {

  Serial.println("DENTRO BUSY ROOM");

  /*
   * value == true, l'aula è occupata
   * value == false, l'aula è libera
   */

  
  if(value == true) {
    //delta calcolato tra start_time e end_time dell'evento in corso
    delta = checkDeltaTimeEvent(et_h, et_m, et_s, st_h, st_m, st_s);

    //Setto i Led e Pin nel caso per l'aula occupata
    setLCDandLed_stanzaOccupata();
  } else {
     //Azzero il delta e setto i Led ed LCD per l'aula senza prenotazione in corso 
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
  root["group_id"] = GROUP_ID;
  root["calendar_id"] = CALENDAR_ID;

  serializeJson(root, Serial);
  Serial.println();
  char shadow[measureJson(root) + 1];
  serializeJson(root, shadow, sizeof(shadow));
    
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
  //Settare il led, bottone e LCD
  pinMode(ledpin1, OUTPUT);
  pinMode(ledpin2, OUTPUT);
  pinMode(button, INPUT);

  // initialize LCD
  lcd.init();
  // turn on LCD backlight                      
  lcd.backlight();

  //Inizializzazione board con stanza libera
  setLCDandLed_stanzaLibera();
  
  Serial.begin(115200);
  delay(1000);
  //myDelay(5000);
  Serial.println();
  Serial.println();

  //Configurazione WiFi e NTPConnect
  WiFi.hostname(THINGNAME);
  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, pass);
  connectToWiFi(String("Trying to connect with SSID: ") + String(ssid));
 
  NTPConnect();
  
  net.setTrustAnchors(&cert);
  net.setClientRSACert(&client_crt, &key);
  client.begin(MQTT_HOST, MQTT_PORT, net);

  //Connessione Mqtt
  connectToMqtt();
  
  /*
   * Inizializzo la node appena accesa quindi richiedo 
   * se vi o meno un evento
   */
  sendData(1);
  
  //Gestione ricezione di un possibile evento 
  client.onMessageAdvanced(messageReceived);
  pmillis = millis();
  Serial.println("VALORE DELTA DOPO MESSAGGIO:");
  Serial.println(delta);
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

      //Se il bottone viene premuto il suo valore è 1
      if (buttonState==1){
          //Gestione casistica nel caso il cui il bottone venga premuto
          Serial.println("Botton ON");
          Serial.println("VALORE DELTA QUANDO BUTTON È 1");
          Serial.println(delta);

          /*
           * Viene inviato un messaggio nel topic solo se: 
           * 
           *  - la board ha status = False (ossia è libera)
           *  - se il delta è maggiore di un'ora (ossia che il prossimo evento
           *    non deve inizare tra meno di un'ora, rendendo possibile
           *    quindi la prenotazione tramite bottone board)
           *  - OPPURE se il delta ha valore 0 (ossia che non vi nessun evento)
           */
          if (status_board == false && (delta > 3600000 || delta == 0)) {
              Serial.println("Dentro add event con button");
              /*
               * Richiamo la funzione per l'invio di un messaggio nel topic
               * per la prenotazione di un'ora tramite bottone della board
               */
              sendData(0);
            } else {
              /*
               * Stampa messaggio di errore nel LCD nel caso
               * in cui non sia possibile prenotare l'aula
               */ 
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
                      if (nextEvent == false) {
                        setLCDandLed_stanzaLibera();
                      } else {
                           setLCDandLed_InfoNextEvent();
                         }
                      }
                  }
              }
          
          delay(200);
          //myDelay(200);
      
    }
  

  /*
   * Gestione dell'attesa (sulla base del valore del delta)
   * dell'inizio corretto della prenotazione.
   * La prenotazione inizia dopo che è trascorso un delta tempo
   */
  currentmillis = millis();
  //Serial.println("VALORE CURRENTMILLIS");
  //Serial.println(currentmillis);

  //Serial.println("VALORE PREVIUS");
  //Serial.println(pmillis);
  
  if ((((currentmillis - pmillis >= delta) && status_board == false) && nextEvent == true) || delta < 0 ){
    Serial.println("Currentmillis in prenotazione aula");
    Serial.println(currentmillis);
    pmillis = currentmillis;
    //Cambia status board, LCD e Pin 
    busyRoom(true);
    Serial.println("Evento programmato: stanza occupata");
    }

  //Questo if serve per liberare l'aula quando è trascorso delta tempo
  if ((currentmillis - pmillis >= delta) && status_board == true) {
     Serial.println("Currentmillis in libera aula");
    Serial.println(currentmillis);
    
    pmillis = currentmillis; 
    //Cambia status board, LCD e Pin
    busyRoom(false);
    nextEvent = false;
    Serial.println("stanza liberata");
    /*
     * Quando la prenotazione finisce, viene inviato un messaggio del topic
     * apposito per richiedere l'aggiornamento (se vi sono eventi prossimi o meno)
     */
    sendData(1); 
    }
}
