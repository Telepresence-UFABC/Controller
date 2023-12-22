#include "/home/nikolas/Documents/GitHub/Controller/arduino/controller/controller.h"

#define pinone 5
#define pintwo 6
#define MAXTIME 5000

uint16_t adcValue = 0;
double error = 0, output = 0, ramp = 0;
unsigned long curr, prev;

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
    error = error; // motor stops running at about 1V
    ramp = (double)(curr - prev) / 1000;
    hBridgeWrite(pinone, pintwo, error > 0 ? error + 1 : error - 1);
    if (curr - prev > MAXTIME)
        prev = millis();
    curr = millis();
    Serial.println(String(ramp, 6) + ", " + String(ramp, 6) + ", " + String(error, 6) + ", " + String(output, 6));
}