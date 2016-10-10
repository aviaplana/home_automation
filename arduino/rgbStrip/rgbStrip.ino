#include <EEPROM.h>
#include <SPI.h>
#include "nRF24L01.h"
#include "RF24.h"

#define DEBUG 1
#define PIN_R 3
#define PIN_G 5
#define PIN_B 6

enum RGB_INSTRUCTION : unsigned char {
  ALL = 0, STORE = 1, ON = 2, OFF = 3, TOGGLE = 4,
  CHANGE_COLOR = 10, CHANGE_FLICK = 11,
  GET_CURRENT = 20, GET_STORED = 21,
  ERR = 63
};

enum PACKET_TYPES : unsigned char {
  PING = 0, CONFIRMATION = 1,
  INIT_REQ = 2, INIT_RES = 3, INIT_INFO_REQ = 4, INIT_INFO_RES = 5, INIT_RESET = 6,  
  RGB = 20
};

struct RGB_PCK {
  unsigned char r;
  unsigned char g;
  unsigned char b;
  unsigned char instruction; //First two bites. First one to know if the light is on or off, the other for the fure
  
  unsigned int ms_flick;
  unsigned int t_dim;
};

struct INIT_INFO_RES_PCK {
  unsigned char pipe;
  unsigned char type;
};

struct INIT_REQ_PCK {
  unsigned int hash;
  unsigned char type; // Node type. In this case, rgb
};

struct INIT_RES_PCK {
  unsigned int hash;
  uint64_t pipe;
};

// Used to send init_req and ping
struct SIMPLE_PCK {
  unsigned char type;
};


struct RET_PACK {
  unsigned char pck_size;
  RGB_PCK pck;
} packet_ret;

union GEN_PACKET {
  RGB_PCK rgb;
  INIT_REQ_PCK init_req;
  INIT_RES_PCK init_res;
  INIT_INFO_RES_PCK init_info_res;
} gen_packet;


//0 to 65,535

//RGB_PCK rgb_packet;

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
unsigned char id;

unsigned int t_dim = 0;
unsigned int ms_flick = 0;
unsigned int dim_tics = 0;
unsigned int dim_int = 30;
unsigned int hash;
unsigned long last_dim = 0;
unsigned long last_flick = 0;

unsigned long test = 0;
uint64_t pipe;
uint64_t main_pipe = 0xF0F0F0F0A1LL; // Address of the main node (manager)
bool initialized = false;

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

  readEeprom(&gen_packet.rgb);
  
  t_dim = gen_packet.rgb.t_dim;
  
  processRgbPacket();

  radio.begin();
  radio.setRetries(15,15);
  radio.setPayloadSize(12);
  radio.enableAckPayload();

  radio.openReadingPipe(1, main_pipe);
  radio.startListening();

  buildInit();
  sendPacket(PACKET_TYPES::INIT_REQ);
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
      flick ? changeLight() : offLight();
      last_flick = millis();
      flick = !flick;
    } 
  }

  if ((millis() - test) > 2000) {
    test = millis();
  }
  
  if (radio.available()) {
    bool done = false;
    char buff[sizeof(gen_packet)+1];
    
    while(!done) {
      done = radio.read(buff, sizeof(gen_packet)+1);
      delay(20);
    }
    
    processPacket(buff);
  }
}

void processPacket(char *buff) {
  unsigned char type = buff[0];
  unsigned char id_p = buff[1];

  // If the node is not initialized, it just waits for initialization packets
  if (!initialized) {
    switch (type) {
      case PACKET_TYPES::INIT_RES:
        id = id_p;
        initialize();
        break;
        
      case PACKET_TYPES::INIT_RESET:
      case PACKET_TYPES::INIT_INFO_REQ:
        buildInit();
        sendPacket(PACKET_TYPES::INIT_REQ);
        break;
    }
  } else {
    switch (type) {
      case PACKET_TYPES::RGB: 
        memcpy(&gen_packet.rgb, buff+1, sizeof(gen_packet.rgb));
        processRgbPacket();
        break;

      case PACKET_TYPES::INIT_RES:
        id = id_p;
        initialize();
        break;
        
      case PACKET_TYPES::INIT_RESET:
        if (id_p == id) {
          buildInit();
          sendPacket(PACKET_TYPES::INIT_REQ);
        }
        break;
        
      case PACKET_TYPES::INIT_INFO_REQ:
        gen_packet.init_info_res.pipe = pipe;
        gen_packet.init_info_res.type = PACKET_TYPES::RGB;
        sendPacket(PACKET_TYPES::INIT_INFO_RES);
        break;
        
      case PACKET_TYPES::PING:
        // Auto acknowledged, nothing to do.
        break;
    }
  }
}

void buildInit() {
  randomSeed(analogRead(0));
  hash = random(65535);

  gen_packet.init_req.hash = hash;
  gen_packet.init_req.type = PACKET_TYPES::RGB;  
  pipe = NULL;
}

void initialize() {
    radio.openReadingPipe(2, pipe);
    initialized = true;
    pipe = gen_packet.init_res.pipe;
}

void readEeprom(RGB_PCK *pack) {
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
  id = EEPROM.read(7);
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
  EEPROM.update(0, gen_packet.rgb.t_dim >> 8);
  EEPROM.update(1, byte(gen_packet.rgb.t_dim));
  EEPROM.update(2, gen_packet.rgb.r);
  EEPROM.update(3, gen_packet.rgb.g);
  EEPROM.update(4, gen_packet.rgb.b);
  EEPROM.update(5, gen_packet.rgb.ms_flick >> 8);
  EEPROM.update(6, byte(gen_packet.rgb.ms_flick));  
  EEPROM.update(7, byte(id)); 
}

void processRgbPacket() {
  // 2 first bites are reserved.
  gen_packet.rgb.instruction &= 0x3F;

  switch (gen_packet.rgb.instruction) {
    
    case RGB_INSTRUCTION::ALL:
      applyFlickPacket();
      applyColorPacket();
      break;
      
    case RGB_INSTRUCTION::STORE:
      gen_packet.rgb.t_dim = t_dim;
      storeDefaults();
      break;
      
    case RGB_INSTRUCTION::ON:
      light_on = true;
      changeLight();
      break;
      
    case RGB_INSTRUCTION::OFF:
      light_on = false;
      offLight();
      break;
      
    case RGB_INSTRUCTION::TOGGLE:
      light_on = !light_on;
      light_on ? changeLight() : offLight() ;
      
      break;
      
    case RGB_INSTRUCTION::CHANGE_COLOR:
      applyColorPacket();
      changeLight();
      break;
      
    case RGB_INSTRUCTION::CHANGE_FLICK:
      applyFlickPacket();
      break;
      
    case RGB_INSTRUCTION::GET_CURRENT:
      packet_ret.pck.r = r;
      packet_ret.pck.g = g;
      packet_ret.pck.b = b;
      packet_ret.pck.ms_flick = ms_flick;
      packet_ret.pck.t_dim = t_dim;
      packet_ret.pck.instruction = RGB_INSTRUCTION::GET_CURRENT;
      
      if (light_on) {
        packet_ret.pck.instruction |= (1 << 7);
      }
      
      sendPacket(PACKET_TYPES::RGB);
      break;
      
    case RGB_INSTRUCTION::GET_STORED:
      readEeprom(&packet_ret.pck);
      packet_ret.pck.instruction = RGB_INSTRUCTION::GET_STORED;
      sendPacket(PACKET_TYPES::RGB);
      break;

    //SEND BACK ERROR
    default:
      packet_ret.pck = gen_packet.rgb;
      packet_ret.pck.instruction = RGB_INSTRUCTION::ERR;
      sendPacket(PACKET_TYPES::RGB);
      break;
  }
}


void applyColorPacket() {
  t_dim = gen_packet.rgb.t_dim;
  
  if (t_dim > 0) {
    dimLight();
  } else {
    r = gen_packet.rgb.r;
    g = gen_packet.rgb.g;
    b = gen_packet.rgb.b; 
     
    changeLight();
  }
}

void applyFlickPacket() {
  changeLight();
  if (flick && ms_flick == 0) {
    flick = false;
  }
  ms_flick = gen_packet.rgb.ms_flick;
  last_flick = millis();
}


void dimLight() {
  dim_tics = round((float)t_dim / (float)dim_int);
  
  r_goal = gen_packet.rgb.r;
  g_goal = gen_packet.rgb.g;
  b_goal = gen_packet.rgb.b;

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


boolean sendPacket(PACKET_TYPES type) {
  radio.stopListening();

  radio.openWritingPipe((type == PACKET_TYPES::INIT_REQ) ? main_pipe : pipe);
  delay(1);
  
  bool ok;
  int size_struct;
  int buff_size;
  char* buff;
  
  switch (type) {
    case PACKET_TYPES::RGB:
      size_struct = sizeof(gen_packet.rgb);
      buff_size = size_struct + 3;
      buff = new byte[buff_size];
      memset(buff, 0, buff_size);
      buff[2] = id;
      
      memcpy(buff + 3, &gen_packet.rgb, size_struct);    
      break;
      
    case PACKET_TYPES::INIT_INFO_RES:
      size_struct = sizeof(gen_packet.init_info_res);
      buff_size = size_struct + 3;
      buff = new byte[buff_size];     
      memset(buff, 0, buff_size);
      buff[2] = id;
      
      memcpy(buff + 3, &gen_packet.init_info_res, size_struct);    
      break;
      
    case PACKET_TYPES::INIT_REQ:
      size_struct = sizeof(gen_packet.init_req);
      buff_size = size_struct + 3;
      buff = new byte[buff_size];    
      memset(buff, 0, buff_size);   
      buff[2] = 0;
      
      memcpy(buff + 3, &gen_packet.init_req, size_struct);   
      break;
      
    default:
      size_struct = 0;
      buff_size = size_struct + 3;
      buff = new byte[3];    
      memset(buff, 0, 3);   
      buff[2] = id;
       
      break;
  }
  
  /*
   * Packet structures:
   * 
     *  | payload length | Type | ID  | payload |
     *           1          1      1       ?      Bytes
     *  
   */
   
  buff[0] = size_struct;      
  buff[1] = type;
  
  ok = radio.write(buff, buff_size);
  radio.startListening(); 
  
  if (DEBUG) {
    Serial.print("SENT: ");
    
    for (int i = 0; i < buff_size; i++) {
      Serial.print((unsigned char)buff[i], HEX);
      Serial.print(" ");
    }
    Serial.println("");
  }

  return ok;
}

