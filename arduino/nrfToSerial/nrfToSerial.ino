#include <SPI.h>
#include "nRF24L01.h"
#include "RF24.h"

#define TYPE_CONFIRMATION 1

byte buffer_ser[35];
byte payloadSize= 10;
byte id;


RF24 radio(9,10);
const uint64_t own_pipe = 0xF0F0F0F0A1LL;
const uint64_t pipes[] = {0xF0F0F0F0A2LL};
byte num_pipes;

void setup() {
  num_pipes = sizeof(pipes) / sizeof(uint64_t);
  radio.begin();
  radio.setRetries(15,15);
  radio.enableDynamicPayloads();
  radio.enableAckPayload();
  radio.openReadingPipe(1, pipes[0]);

  radio.startListening();
  Serial.begin(9600);
  
  memset(buffer_ser, 0, 35);
}


void loop() {
  if (checkMsg() && id <= num_pipes) {
    radio.stopListening();
    radio.openWritingPipe(pipes[id-1]);
    delay(1);
    
    bool ok = radio.write(&buffer_ser, payloadSize);
            
    radio.startListening();
    delay(2);
    
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
    
    while (!done)
    {
      done = radio.read(&buffer_ser, pay_size);
      delay(20);
    }

    /*
     * radio packet structure:
     *  | Type | payload length | payload |
     *     1            1            ?      Bytes
     *     
     * Serial packet structure:
     *  | \B | Type | ID | payload | \E | 
     *     2    1      1     ?       2     Bytes
     */
    Serial.print("\\B");
    Serial.write(buffer_ser[0]); //type 
    for (int i = 0; i < buffer_ser[1]; i++) {
      Serial.write(buffer_ser[i + 2]);
    }
    Serial.print("\\E");
  }
}


bool checkMsg() {
  int pos = 0;
  int pre_end = 0;

  /*
   * Packet structure:
   * | \B | id | payload | \E |
   *   2     1      ?       2   Bytes
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
   
    /*
    } else if (pos == 3) {
      payloadSize = c;
    } else if (((pos - 4) < payloadSize) && (pos > 3 )) {
      buffer_ser[pos - 4] = c;
    }
    */
    delay(2);
    pos++;
    
  }
  
  return false;
}

