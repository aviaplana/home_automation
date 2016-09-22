#include <SPI.h>
#include <avr/sleep.h>
#include <avr/power.h>
#include <avr/wdt.h>
#include "nRF24L01.h"
#include "RF24.h"

enum INSTRUCTION : unsigned char {
  VOLTAGE = 0, NEW_MAIL = 1, DOOR_OPEN = 2,
  ERR = 63
};


struct INST_PCK {
  unsigned char id = 2;
  unsigned int voltage;
  unsigned char instruction;
} packet;


struct RET_PACK {
  unsigned char type = 11;
  unsigned char pck_size = sizeof(packet);
  INST_PCK pck;
} packet_ret;


RF24 radio(9,10);

// Radio pipe addresses for the 2 nodes to communicate.
const uint64_t pipe = 0xF0F0F0F0A3LL;

unsigned long last_int = 0;
volatile boolean flag_int = false;
volatile int watchdog_bites = 0;

void setup(void)
{
  disableWatchdog();
  pinMode(2, INPUT_PULLUP);
  Serial.begin(57600);

  radio.begin();
  radio.setRetries(15,15);
  radio.setPayloadSize(8);

  radio.openWritingPipe(pipe);
  attachInterrupt(digitalPinToInterrupt(2), intMail, LOW);
}

void loop(void)
{ 
    if (flag_int)  {
      flag_int = false;
      radio.powerUp();
      delay(1);
      
      packet_ret.pck.instruction = INSTRUCTION::NEW_MAIL;
      packet_ret.pck.voltage = 33;
      
      bool ok = radio.write(&packet_ret, sizeof(packet_ret));
      
      if (ok)
        Serial.println("...ok");
      else
        Serial.println("...failed");
        
      radio.powerDown();
      delay(50);

      // Wait for 16 seconds to enable interrupts 
      while (watchdog_bites < 2) {
        enableWatchdog();  
      }
      
  } else if (watchdog_bites >= 2) {
    watchdog_bites = 0;
    disableWatchdog();
    attachInterrupt(digitalPinToInterrupt(2), intMail, LOW);  
  }

  sleepNow();
}

void disableWatchdog()
{
  wdt_disable();
}

void enableWatchdog()
{
  set_sleep_mode(SLEEP_MODE_PWR_DOWN);

  // disable interrupts
  cli();
  
  // Clear previous watchdog reset
  MCUSR &= ~(1<<WDRF); 

  //Enable changes
  WDTCSR |= (1<<WDCE) | (1<<WDE); 

  // 8 seconds
  WDTCSR = ((1<<WDP0) | (1<<WDP1) | (1<<WDP2) | (1<<WDP3));

  // Enable only watchdog interrupts
  WDTCSR |= (1 << WDIE);
  
  // Enable interrupts
  sei();

  sleep_enable(); 
  sleep_mode(); 
  sleep_disable();
}

void sleepNow()         // here we put the arduino to sleep
{
    set_sleep_mode(SLEEP_MODE_PWR_DOWN);   // sleep mode is set here
 
    sleep_enable();          // enables the sleep bit in the mcucr register
                             // so sleep is possible. just a safety pin
 
 
    sleep_mode();            // here the device is actually put to sleep!!
                             // THE PROGRAM CONTINUES FROM HERE AFTER WAKING UP
 
    sleep_disable();         // first thing after waking from sleep:
                             // disable sleep...
    detachInterrupt(0);      // disables interrupt 0 on pin 2 so the
                             // wakeUpNow code will not be executed
                             // during normal running time.
 
}

ISR (WDT_vect)
{ 
  watchdog_bites++;
}

void intMail()
{
  flag_int = true;
}

