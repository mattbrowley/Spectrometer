#define CLK PORTB2 // digital pin 10, chip pin 16
#define ROG PORTB1 // digital pin 9, chip pin 15
#define START PORTB0 // digital pin 8, chip pin 14
#define LED PORTB5 // digital pin 13, chip pin 19
#define INI 2 // pulse from due to initiate a ROG pulse

volatile bool pulsed;
volatile bool do_ROG;

int delay_time = 4;

void setup(){ 
  DDRB = B00100111;
  PORTB = (1 << CLK) | (1 << ROG) | (0 << START) | (0 << LED);
  pulsed = 0;
  do_ROG = 0;
  attachInterrupt(INI, set_ROG, RISING);
}

void loop(){
  if (pulsed){
    sendStart();
  }
  if (do_ROG){
    ROGPulse();
  }
  if (!pulsed && !do_ROG){
    clockTick();
  }
}

void clockTick(){
  PORTB = (0 << CLK) | (1 << ROG) | (0 << START) | (0 << LED);
  delayMicroseconds(delay_time);
  PORTB = (1 << CLK) | (1 << ROG) | (0 << START) | (0 << LED);
  delayMicroseconds(delay_time-1);
}

void set_ROG(){
  do_ROG = 1;
}

void ROGPulse(){  
  PORTB = (0 << CLK) | (1 << ROG) | (0 << START) | (0 << LED);
  delayMicroseconds(delay_time);
  PORTB = (1 << CLK) | (1 << ROG) | (0 << START) | (0 << LED);
  delayMicroseconds(1);
  PORTB = (1 << CLK) | (0 << ROG) | (0 << START) | (0 << LED);
  delayMicroseconds(5);
  PORTB = (1 << CLK) | (1 << ROG) | (0 << START) | (0 << LED);
  delayMicroseconds(2);
  do_ROG = 0;
  pulsed = 1;
}

void sendStart(){
  // Cycle through dummy signals 32
  for (int i = 0; i < 32; i++){
    clockTick();
  }
  // Send the start signal for a clock cycles
  PORTB = (0 << CLK) | (1 << ROG) | (1 << START) | (1 << LED);
  delayMicroseconds(delay_time);
  PORTB = (1 << CLK) | (1 << ROG) | (1 << START) | (1 << LED);
  delayMicroseconds(delay_time);  
  pulsed = 0;
}
