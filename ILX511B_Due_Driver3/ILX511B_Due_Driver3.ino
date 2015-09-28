#define VOut A0 // Analog input from CCD
#define START 4 // Digital input from Slave_Clock
#define CLK 26 // Clock signal to trigger interrupts
#define INI 2 // Signal to send to clock to initiate ROG pulse

volatile int data[2048];
volatile int pixel;
volatile bool reading;
bool indicator = 0;

void setup() {
  Serial.begin(115200);
  establishContact();
  pinMode(START, INPUT);
  pinMode(CLK, INPUT);
  pinMode(INI, OUTPUT);
  digitalWrite(INI, 0);
  pinMode(13, OUTPUT);
  digitalWrite(13, indicator);
  reading = 0;
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
    readLine();    
    sendData();
    indicator = !indicator;
    digitalWrite(13, indicator);
  }
}

void initiateScan(int i_time) {
  int start_time = millis();
  digitalWrite(INI, 1);
  digitalWrite(INI, 0);
  while(millis() < start_time + i_time) ;
  digitalWrite(INI, 1);
  digitalWrite(INI, 0);
  reading = 0;
}

void readPixel(){
  if (pixel < 2048 && reading){
    pixel++;
    while((ADC->ADC_ISR & 0x80)==0); // wait for conversion
    data[pixel]=ADC->ADC_CDR[7];              // read data    
  }
  else{
    reading = 0;
  }
  
}

void beginRead() {
  reading = 1;
}

void readLine() {
  pixel = 0;
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

