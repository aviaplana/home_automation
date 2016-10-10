#include <SPI.h>
#include "nRF24L01.h"
#include "RF24.h"
#include "nodelist.h"

#define TYPE_CONFIRMATION 1

enum MAIN_INSTRUCTION : unsigned char {
  ADD_NODE = 0, DELETE_NODE = 1, DELETE_LIST = 2
};

byte buffer_ser[35];
byte payloadSize = 10;
byte id;

NodeList* node_list = new NodeList();

RF24 radio(9,10);
const uint64_t own_pipe = 0xF0F0F0F0A1LL;
const uint64_t pipe_mask = 0xF0F0F0F000LL;

void setup() {  
  radio.begin();
  radio.setRetries(15,15);
  radio.enableDynamicPayloads();
  radio.enableAckPayload();
  radio.openReadingPipe(1, own_pipe);

  radio.startListening();
  Serial.begin(9600);
  
  memset(buffer_ser, 0, 35);
}


void loop() {
  // id: 0-Broadcast, 1-Main node, else-nodes
  if (checkMsg()) {// && id <= num_pipes) {
    bool ok;
    
    if (id == 1) {
      ok = processInstruction();
      // Message for this node
    } else {
      radio.stopListening();
      bool can_send = true;
      if (id == 0) {
        // Broadcast
        radio.openWritingPipe(own_pipe);
      } else {
        unsigned char n_id = buffer_ser[1];
        // Check if id exist in list
        byte pipe = node_list->getPipe(n_id);
        if (pipe) {
          radio.openWritingPipe((uint64_t) pipe_mask + pipe); 
        } else {
          can_send = false;
        }
      }
      
      if (can_send) {
        delay(1);
        ok = radio.write(&buffer_ser, payloadSize);
        
        radio.startListening();
        delay(2);
      }
    }
    
    Serial.print("\\B");
    Serial.write((byte)TYPE_CONFIRMATION);
    Serial.write(id);
    Serial.write(ok);
    Serial.print("\\E");
  }

  if (radio.available()) {
    int pay_size = radio.getPayloadSize();
    memset(buffer_ser, 0, pay_size);
    bool done = false;
    
    while (!done) {
      done = radio.read(&buffer_ser, pay_size);
      delay(20);  
    }

    /*
     * radio packet structure:
     *  | payload length | Type | ID (*) | payload |
     *           1          1      1       ?      Bytes
     *  
     *  * NOT USED IF PACKET TYPE = INIT_SEQ
     *     
     * Serial packet structure:
     *  | \B | Type | ID | payload | \E | 
     *     2    1      1     ?       2     Bytes
     */
    Serial.print("\\B");
    Serial.write(buffer_ser[1]);
    Serial.write(buffer_ser[2]);
    
    for (int i = 0; i < buffer_ser[0]; i++) {
      Serial.write(buffer_ser[i + 3]);
    }
    
    Serial.print("\\E");
  }
}

boolean processInstruction() {
  unsigned char type = buffer_ser[0];
  unsigned char n_id;
  byte n_pipe;
  boolean ret_val = true;
  
  switch (type) {
    case MAIN_INSTRUCTION::ADD_NODE:
      n_id = buffer_ser[1];
      n_pipe = buffer_ser[2];
      ret_val = node_list->addNode(n_id, n_pipe);
      break;
      
    case MAIN_INSTRUCTION::DELETE_NODE:
      n_id = buffer_ser[1];
      node_list->deleteNode(n_id);
      break;
      
    case MAIN_INSTRUCTION::DELETE_LIST:
      node_list->deleteAll();
      break;
  }

  return ret_val;
}

bool checkMsg() {
  int pos = 0;
  int pre_end = 0;

  /*
   * Packet structure:
   * | \B | id | type | payload | \E |
   *   2     1     1        ?      2   Bytes
   */
  while (Serial.available()) {
    byte c = Serial.read();

    if (pos == 0) {
      if (c != '\\') {
        pos = 0;
        continue;
      }
    } else if (pos == 1) {
      if (c != 'B') {
        pos = 0;
        continue;
      }
    } else if (pos == 2) {
      id = c;
    } else if (c == '\\') {
      pre_end = pos;
    } else if ((pre_end + 1 == pos) && (c == 'E')) {
      payloadSize = pos - 4; // \B + id + \E = 5 Bytes - 1 (position 0).
      return true;
    } else {
      buffer_ser[pos - 3] = c;      
    } 
    
    delay(2);
    pos++;
    
  }
  
  return false;
}

