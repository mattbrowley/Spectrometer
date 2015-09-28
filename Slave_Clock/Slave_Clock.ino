#include <Wire.h>

#define CLK PORTB2 // digital pin 10, chip pin 16
#define ROG PORTB1 // digital pin 9, chip pin 15
#define START PORTB0 // digital pin 8, chip pin 14
#define LED PORTB5 // digital pin 13, chip pin 19

int delay_time = 4;
int last_ROG = 0;

void setup(){ 
  Wire.begin(4);
  Wire.onReceive(startScan);
  DDRB = B00100111;
  PORTB = (1 << CLK) | (1 << ROG) | (0 << START) | (0 << LED);
}

void loop(){
  clockTick();
}

void clockTick(){
  PORTB = (0 << CLK) | (1 << ROG) | (0 << START) | (0 << LED);
  delayMicroseconds(delay_time);
  PORTB = (1 << CLK) | (1 << ROG) | (0 << START) | (0 << LED);
  delayMicroseconds(delay_time);
}

void startScan(int numBytes){  
  PORTB = (0 << CLK) | (1 << ROG) | (0 << START) | (0 << LED);
  delayMicroseconds(delay_time);
  PORTB = (1 << CLK) | (1 << ROG) | (0 << START) | (0 << LED);
  delayMicroseconds(1);
  PORTB = (1 << CLK) | (0 << ROG) | (0 << START) | (0 << LED);
  delayMicroseconds(3);
  PORTB = (1 << CLK) | (1 << ROG) | (0 << START) | (0 << LED);
  delayMicroseconds(1);
  /*int start_time = millis();  
  int integration_time = Wire.read()<<8 | Wire.read(); 
  //Serial.print(start_time);
  while(millis() < start_time + integration_time){
    clockTick();
  }*/
  for (int i = 0; i < 500; i++){
    clockTick();
  }
  PORTB = (0 << CLK) | (1 << ROG) | (0 << START) | (0 << LED);
  delayMicroseconds(delay_time);
  PORTB = (1 << CLK) | (1 << ROG) | (0 << START) | (0 << LED);
  delayMicroseconds(1);
  PORTB = (1 << CLK) | (0 << ROG) | (0 << START) | (0 << LED);
  delayMicroseconds(5);  
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
  //delayMicroseconds(delay_time);
}
