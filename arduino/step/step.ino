#include "/home/nikolas/Documents/GitHub/Controller/arduino/controller/controller.h"

#define pinone 5
#define pintwo 6
#define MAXTIME 5000

uint16_t adcValue = 0;
double error = 0, output = 0, ref = 1.0, time = 0;

void setup()
{
    Serial.begin(115200);
    Serial.println("Tempo, Referencia, Erro, Posicao");
}

void loop()
{
    adcValue = analogRead(0);
    output = (double)adcValue / 1023 * 5;
    error = ref - output;
    time = (double)millis()/1000;
    hBridgeWrite(pinone, pintwo, error > 0 ? error + 1 : error - 1);
    Serial.println(String(time, 6) + ", " + String(ref, 6) + ", " + String(error, 6) + ", " + String(output, 6));
}