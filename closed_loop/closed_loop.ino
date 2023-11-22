#include "/home/nikolas/Documents/GitHub/Controller/controller/controller.h"

#define pinone 5
#define pintwo 6
#define MAXTIME 5000

uint16_t adcValue = 0;
double error = 0, output = 0, ramp = 0, outputSamples, rampSamples;
unsigned long curr, prev, time;

void setup()
{
    Serial.begin(115200);
    Serial.println("Tempo, Referencia, Erro, Posicao");
}

void loop()
{
    adcValue = analogRead(0);
    output = (double)adcValue / 1023 * 5;
    error = ramp - output;
    error = error > 0 ? error + 1 : error - 1; // motor stops running at about 1V
    ramp = (double)(curr - prev) / 1000;
    hBridgeWrite(pinone, pintwo, error);
    if (curr - prev > MAXTIME)
        prev = millis();
    curr = millis();
    Serial.println(String(ramp) + ", " + String(ramp) + ", " + String(error > 0 ? error - 1: error + 1) + ", " + String(output));
}