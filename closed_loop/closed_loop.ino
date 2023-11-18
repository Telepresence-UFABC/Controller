#include "/home/nikolas/Documents/GitHub/Controller/controller/controller.h"

#define pinone 5
#define pintwo 6
#define MAXTIME 5000
#define MAXSAMPLES 3000

uint16_t adcValue = 0, count = 0;
double error = 0, output = 0, ramp = 0, outputSamples[MAXSAMPLES], rampSamples[MAXSAMPLES];
unsigned long curr, prev, time[MAXSAMPLES];
char buffer[50];

void setup()
{
    Serial.begin(115200);
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
    sprintf(buffer, "Referencia: %lf\nErro: %lf\n", ramp, error);
    Serial.print(buffer);

    // store time, reference and output until maximum amount
    if (count < MAXSAMPLES)
    {
        time[count] = curr;
        rampSamples[count] = ramp;
        outputSamples[count] = output;
        count++;
    }
    // print data and halt after data collection
    else
    {
        Serial.println("Tempo, Rampa, Saida");
        for (int i = 0; i < MAXSAMPLES; i++)
        {
            sprintf(buffer, "%lf, %lf, %lf\n", time[i], rampSamples[i], outputSamples[i]);
            Serial.print(buffer);
        }
        while (true)
        {
        }
    }
}