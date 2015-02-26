/* Spec_Duino_Fake
   Author: Matt Rowley
   
   This will interface with the python script exactly like
   the final real arduino sketch will. Rather than collect
   real data, it generates fake data.
*/


void setup(){
  Serial.begin(115200);
  establishContact();
}

void loop(){
  if (Serial.available() > 0){
    int integration_time = Serial.parseInt();
    while (Serial.available() > 0 ){
      Serial.read(); // Clear the serial buffer
    }
    int center = random(500) + 774;
    int amp = random(500) + 3500;
    for (int i = 0; i < 2048; i++){
      
      unsigned int data = int(amp * pow(2.7,-(double(i-center)*(i-1024)/160000)) + random(200));      
      Serial.write(byte(data>>8)); // high byte
      Serial.write(byte(data)); // low byte      
    }
  }
  delay(2);
}

void establishContact(){
  Serial.println("Spec");
}
