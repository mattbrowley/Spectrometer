#include <Wire.h>

#define CLK PORTB2 // digital pin 10, chip pin 16
#define ROG PORTB1 // digital pin 9, chip pin 15
#define START PORTB0 // digital pin 8, chip pin 14
#define LED PORTB5 // digital pin 13, chip pin 19

int delay_time = 4;
int last_ROG = 0;
volatile int integration_time = 0;
volatile bool start = 0;

void setup(){ 
  Wire.begin(4);
  Wire.onReceive(startScan);
  DDRB = B00100111;
  PORTB = (1 << CLK) | (1 << ROG) | (0 << START) | (0 << LED);
}

void loop(){
  clockTick();
  if(start){
    clockTick();clockTick();clockTick();clockTick();clockTick();clockTick();clockTick();
    runScan();
    clockTick();clockTick();clockTick();clockTick();clockTick();
  }
  clockTick();
}

void clockTick(){
  PORTB = (0 << CLK) | (1 << ROG) | (0 << START) | (0 << LED);
  delayMicroseconds(delay_time);
  PORTB = (1 << CLK) | (1 << ROG) | (0 << START) | (0 << LED);
  delayMicroseconds(delay_time);
}

void startScan(int numbBytes){
  start = 1;
  integration_time = Wire.read();
}

void runScan(){  
  PORTB = (0 << CLK) | (1 << ROG) | (0 << START) | (0 << LED);
  delayMicroseconds(delay_time);
  PORTB = (1 << CLK) | (1 << ROG) | (0 << START) | (0 << LED);
  delayMicroseconds(1);
  PORTB = (1 << CLK) | (0 << ROG) | (0 << START) | (0 << LED);
  delayMicroseconds(3);
  PORTB = (1 << CLK) | (1 << ROG) | (0 << START) | (0 << LED);
  
  unsigned long start_time = micros();
  start=0;
  unsigned long end_time = start_time + 1000 * integration_time;
  while(micros() < end_time){
    PORTB = (0 << CLK) | (1 << ROG) | (0 << START) | (0 << LED);
    delayMicroseconds(delay_time);
    PORTB = (1 << CLK) | (1 << ROG) | (0 << START) | (0 << LED);
  }
  PORTB = (0 << CLK) | (1 << ROG) | (0 << START) | (0 << LED);
  delayMicroseconds(delay_time);
  PORTB = (1 << CLK) | (1 << ROG) | (0 << START) | (0 << LED);
  delayMicroseconds(1);
  PORTB = (1 << CLK) | (0 << ROG) | (0 << START) | (0 << LED);
  delayMicroseconds(3);  
  PORTB = (1 << CLK) | (1 << ROG) | (0 << START) | (0 << LED);
  delayMicroseconds(2);
  // Cycle through 32 dummy signals
  for (int i = 0; i < 32; i++){
    clockTick();
  }
  // Send the start signal for one clock cycles
  PORTB = (0 << CLK) | (1 << ROG) | (1 << START) | (1 << LED);
  delayMicroseconds(delay_time);
  PORTB = (1 << CLK) | (1 << ROG) | (1 << START) | (1 << LED);
  delayMicroseconds(delay_time);
}
