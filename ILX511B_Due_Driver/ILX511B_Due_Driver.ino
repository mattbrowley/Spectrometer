#define VOut A0 // Analog input from CCD
#define ROG 4 // Digital input from Slave_Clock
#define CLK 26 // Clock signal to trigger interrupts

#include <Wire.h>

volatile int data[2048];
volatile int pixel;
volatile bool reading;
bool indicator = 0;

void setup() {
  analogReadResolution(12);
  Serial.begin(115200); //230400
  establishContact();  
  Wire.begin();
  //Wire.beginTransmission(4);
  pinMode(START, INPUT);
  pinMode(CLK, INPUT);
  pinMode(13, OUTPUT);
  digitalWrite(13, indicator);
  reading = 0;
  pixel = 0;
  ADC->ADC_MR |= 0x80; // these lines set free running mode on adc 7 (pin A0)
  ADC->ADC_CR=2;
  ADC->ADC_CHER=0x80;
  attachInterrupt(CLK, readPixel, RISING);
  attachInterrupt(START, beginRead, FALLING);
}

void loop() {
  if (Serial.available() > 0){
    int i_time = Serial.parseInt();
    while (Serial.available() > 0 ){
      Serial.read();
    }
    initiateScan(i_time);    
    while(!reading);
    //delay(i_time);
    readLine();    
    sendData();
    indicator = !indicator;
    digitalWrite(13, indicator);
  }
}

void initiateScan(int i_time) {
  Wire.beginTransmission(4);
  Wire.write(i_time);
  Wire.endTransmission();
}

void readPixel(){
  if (pixel < 2048 && reading){
    pixel++;
    while((ADC->ADC_ISR & 0x80)==0); // wait for conversion
    data[pixel]=ADC->ADC_CDR[7];              // read data
    //data[pixel]=analogRead(VOut);
    
  }
  else{
    reading = 0;
  }
  
}

void beginRead() {  
  reading = 1;
  pixel = 0;
}

void readLine() {
  while(reading);
}

void sendData() {
  for (int i=0; i<2048;i++){
    Serial.write(byte(data[i]>>8)); // high byte
    Serial.write(byte(data[i])); // low byte  
  }
  Serial.flush();
}

void establishContact(){
  Serial.println("Spec");
  delay(20);
  Serial.println("Spec");
}

