#include "/home/nikolas/GitHub/Controller/controller/controller.h"

#define pinone 5
#define pintwo 6
#define MAXTIME 1e3

uint16_t adcValue = 0;
double error = 0, prevOutput = 0, output = 0, speed, ref = 5, deltaT, tempo;
unsigned long curr, prev = 0;

void setup()
{
    Serial.begin(115200);
    Serial.println("Tempo, Velocidade");
}

void loop()
{
    curr = micros();
    adcValue = analogRead(0);
    hBridgeWrite(pinone, pintwo, ref);
    if(curr-prev>MAXTIME){
      deltaT = (double)(curr-prev)/1e6;
      tempo = (double)curr/1e6;
      prevOutput = output;
      output = (double)adcValue / 1023 * 5;
      speed = (output-prevOutput)/deltaT;
      Serial.println(String(tempo, 6) + ", " + String(speed, 6));
      prev = curr;
    }
}