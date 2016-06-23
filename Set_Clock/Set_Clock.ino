#include <Wire.h>

const int ds_address = 0xB0 >> 1; // The DS1077 default address from its datasheet is 10110000,
                                  // or B0 in hex, but the wire library drops the read/write
                                  // bit and instead uses different read/write functions.
                                  
int kHz = 100;  // This is the clock frequency in kHz
void setup() {
  pinMode(13,OUTPUT);
  digitalWrite(13,0);
  Wire.begin();
  delay(100);
  Wire.beginTransmission(ds_address);
  Wire.write(B00001101); // Write to the BUS register 
  Wire.write(B00001000); // keep address at 000, and defer writing to EEPROM
  Wire.endTransmission();
  delay(100);
  Wire.beginTransmission(ds_address);
  Wire.write(B00000010);  // Write to the MUX register
  Wire.write(B00000110);  // Sets CTRL0 as powerdown (on high), disables Out0
  Wire.write(B10000000);  // Sets prescaler1 to 2
  Wire.endTransmission();
  delay(100);
  byte high_byte;
  byte low_byte;
  long divisor;
  // find the appropriate DIV register bits
  divisor = 133333 / (2*kHz);
  high_byte = divisor >> 2;  // The high byte is really bits 2 - 10
  low_byte = divisor << 8;  // Legacy code alert! 
                            // This always sets the low byte to 0, perhaps it should have
                            // been shifted by only << 6 to make bits 0-1 with right-
                            // padded 0s. . . Test this with the oscilloscope, I guess.
  Wire.beginTransmission(ds_address);
  Wire.write(B00000001);  // Write to the DIV register
  Wire.write(high_byte);
  Wire.write(low_byte);
  Wire.endTransmission();
  delay(100);
  Wire.beginTransmission(ds_address);
  Wire.write(B00111111); // Write the current register states to EEPROM 
  Wire.endTransmission();
}

void loop() {
  digitalWrite(13,1);
  delay(1000);
  digitalWrite(13,0);
  delay(1000);
  // put your main code here, to run repeatedly:

}
