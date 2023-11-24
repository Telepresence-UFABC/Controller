#include "/home/nikolas/Documents/GitHub/Controller/controller/controller.h"

#define pinone 5
#define pintwo 6
#define MAXTIME 25

uint16_t adcValue = 0;
double error = 0, prevOutput = 0, output = 0, speed, ref = 5, tempo;
unsigned long curr, prev = 0;

void setup()
{
    Serial.begin(9600);
    Serial.println("Tempo, Velocidade");
}

void loop()
{
    curr = millis();
    adcValue = analogRead(0);
    hBridgeWrite(pinone, pintwo, ref > 0 ? ref + 1 : ref - 1);
    if(curr-prev>MAXTIME){
      tempo = (double)(curr-prev)/1000;
      prevOutput = output;
      output = (double)adcValue / 1023 * 5;
      speed = (output-prevOutput)/tempo;
      Serial.println(String((double)(millis())/1000, 6) + ", " + String(speed, 6));
      prev = curr;
    }
}