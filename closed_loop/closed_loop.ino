#include "/home/nikolas/Documents/GitHub/Controller/controller/controller.h"

#define pinone 5
#define pintwo 6
#define MAXTIME 5000

uint16_t adcValue = 0;
double error = 0, voltage = 0, ramp = 0;
unsigned long curr, prev;
char buffer[50];

void setup()
{
    Serial.begin(115200);
}

void loop()
{
    adcValue = analogRead(0);
    voltage = (double)adcValue / 1023 * 5;
    error = ramp - voltage;
    error = error > 0 ? error + 1 : error - 1; // motor stops running at about 1V
    ramp = (double)(curr - prev) / 1000;
    hBridgeWrite(pinone, pintwo, error);
    if (curr - prev > MAXTIME)
        prev = millis();
    curr = millis();
    sprintf(buffer, "Referencia: %lf\nErro: %lf\n", ramp, error);
    Serial.print(buffer);
}
