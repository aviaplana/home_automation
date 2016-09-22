#include <EEPROM.h>
#include <SPI.h>
#include "nRF24L01.h"
#include "RF24.h"

#define DEBUG 0
#define PIN_R 3
#define PIN_G 5
#define PIN_B 6

enum INSTRUCTION : unsigned char {
  ALL = 0, STORE = 1, ON = 2, OFF = 3, TOGGLE = 4,
  CHANGE_COLOR = 10, CHANGE_FLICK = 11,
  GET_CURRENT = 20, GET_STORED = 21,
  ERR = 63
};

struct INST_PCK {
  unsigned char id = 1;
  unsigned char r;
  unsigned char g;
  unsigned char b;
  unsigned char instruction; //First two bites. First one to know if the light is on or off, the other for the fure
  
  unsigned int ms_flick;
  unsigned int t_dim;
} packet;

struct RET_PACK {
  unsigned char type = 10;
  unsigned char pck_size = sizeof(packet);
  INST_PCK pck;
} packet_ret;

RF24 radio(9,10);

bool flick = false;
bool light_on = true;

float r;
float g;
float b;

float r_int;
float g_int;
float b_int;

unsigned char r_goal;
unsigned char g_goal;
unsigned char b_goal;

unsigned int ms_flick = 0;
unsigned int dim_tics = 0;
unsigned int dim_int = 30;
unsigned long last_dim = 0;
unsigned long last_flick = 0;

const uint64_t pipe = 0xF0F0F0F0A2LL;

void setup() {
  pinMode(PIN_R, OUTPUT);
  pinMode(PIN_G, OUTPUT);
  pinMode(PIN_B, OUTPUT);
  
  if (DEBUG) {
    Serial.begin(9600);
  }
  
  r = 0;
  g = 0;
  b = 0;

  readEeprom(&packet);
  
  processPacket();

  radio.begin();
  radio.setRetries(15,15);
  radio.enableDynamicPayloads();
  radio.enableAckPayload();
  
  radio.openReadingPipe(1,pipe);
  radio.startListening();
}

void loop() {
  if (light_on) {
    if (dim_tics > 0 && ((millis() - last_dim) > dim_int)) {
      dimLed(&r, r_int, r_goal);
      dimLed(&g, g_int, g_goal);
      dimLed(&b, b_int, b_goal);
  
      dim_tics--;
      last_dim = millis();
      if (!flick) {
        changeLight();
      }
    } 
  
    if ((ms_flick > 0) && ((millis() - last_flick) > ms_flick)) {
      flick ? offLight() : changeLight();
      last_flick = millis();
      flick = !flick;
    } 
  }
  
  
  if (radio.available()) {
    bool done = false;
    while (!done)
    {
      done = radio.read(&packet, sizeof(packet));
      delay(20);
    }

    processPacket();
  }
}

void readEeprom(INST_PCK *pack) {
  pack->r = 0;
  pack->g = 0;
  pack->b = 0;
  pack->t_dim = 0;
  pack->ms_flick = 0;
  
  pack->t_dim |= ((EEPROM.read(0) << 8) + (EEPROM.read(1)));
  pack->r = EEPROM.read(2);
  pack->g = EEPROM.read(3);
  pack->b = EEPROM.read(4);
  pack->ms_flick |= ((EEPROM.read(5) << 8) + (EEPROM.read(6)));
  pack->id = EEPROM.read(7);
}

void dimLed(float *color, float inc, unsigned char goal) {
  float temp = *color + inc;
  if ((inc > 0 ) && (temp > goal)) {
    *color = goal;
  } else if ((inc < 0 ) && (temp < 0)) {
    *color = 0;
  } else {
    *color = temp;
  }
}

void storeDefaults() {
  EEPROM.update(0, packet.t_dim >> 8);
  EEPROM.update(1, byte(packet.t_dim));
  EEPROM.update(2, packet.r);
  EEPROM.update(3, packet.g);
  EEPROM.update(4, packet.b);
  EEPROM.update(5, packet.ms_flick >> 8);
  EEPROM.update(6, byte(packet.ms_flick));  
  EEPROM.update(7, byte(packet.id)); 
}

void processPacket() {
  // 2 first bites are reserved.
  packet.instruction &= 0x3F;
  
  switch (packet.instruction) {
    
    case INSTRUCTION::ALL:
      applyFlickPacket();
      applyColorPacket();
      break;
      
    case INSTRUCTION::STORE:
      storeDefaults();
      break;
      
    case INSTRUCTION::ON:
      light_on = true;
      changeLight();
      break;
      
    case INSTRUCTION::OFF:
      light_on = false;
      offLight();
      break;
      
    case INSTRUCTION::TOGGLE:
      light_on = !light_on;
      light_on ? changeLight() : offLight() ;
      
      break;
      
    case INSTRUCTION::CHANGE_COLOR:
      applyColorPacket();
      changeLight();
      break;
      
    case INSTRUCTION::CHANGE_FLICK:
      applyFlickPacket();
      break;
      
    case INSTRUCTION::GET_CURRENT:
      packet_ret.pck.r = r;
      packet_ret.pck.g = g;
      packet_ret.pck.b = b;
      packet_ret.pck.ms_flick = ms_flick;
      // Nonsense since it's being overriden every time we receive a packet.
      packet_ret.pck.t_dim = packet.t_dim;
      packet_ret.pck.instruction = INSTRUCTION::GET_CURRENT;
      
      if (light_on) {
        packet_ret.pck.instruction |= (1 << 7);
      }
      
      sendPacket();
      break;
      
    case INSTRUCTION::GET_STORED:
      readEeprom(&packet_ret.pck);
      packet_ret.pck.instruction = INSTRUCTION::GET_STORED;
      sendPacket();
      break;

    //SEND BACK ERROR
    default:
      packet_ret.pck = packet;
      packet_ret.pck.instruction = INSTRUCTION::ERR;
      sendPacket();
      break;
  }
}


void applyColorPacket() {
  if (packet.t_dim > 0) {
    dimLight();
  } else {
    r = packet.r;
    g = packet.g;
    b = packet.b; 
     
    changeLight();
  }
}

void applyFlickPacket() {
  changeLight();
  ms_flick = packet.ms_flick;
  last_flick = millis();
}


void dimLight() {
  dim_tics = round((float)packet.t_dim / (float)dim_int);
  
  r_goal = packet.r;
  g_goal = packet.g;
  b_goal = packet.b;

  r_int = (r_goal - r) / (float)dim_tics;
  g_int = (g_goal - g) / (float)dim_tics;
  b_int = (b_goal - b) / (float)dim_tics;
}

void changeLight() {
  analogWrite(PIN_R, round(r));
  analogWrite(PIN_G, round(g));
  analogWrite(PIN_B, round(b));    
}

void offLight() {
  analogWrite(PIN_R, 0);
  analogWrite(PIN_G, 0);
  analogWrite(PIN_B, 0);    
}

boolean sendPacket() {
  radio.stopListening();

  radio.openWritingPipe(pipe);
  delay(1);
  
  bool ok = radio.write(&packet_ret, sizeof(packet_ret));
  
  radio.startListening(); 
  
  if (DEBUG) {
    Serial.print("SENT: ");
    Serial.print(packet_ret.type);
    Serial.print(" ");
    Serial.print(packet_ret.pck_size);
    Serial.print(" ");
    Serial.print(packet_ret.pck.r);
    Serial.print(" ");
    Serial.print(packet_ret.pck.g);
    Serial.print(" ");
    Serial.print(packet_ret.pck.b);
    Serial.print(" ");
    Serial.print(packet_ret.pck.instruction);
    Serial.print(" ");
    Serial.print(packet_ret.pck.ms_flick);
    Serial.print(" ");
    Serial.print(packet_ret.pck.t_dim);
    Serial.println(" ");
  }

  return ok;
}

