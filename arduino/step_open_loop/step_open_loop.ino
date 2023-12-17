#include "/home/nikolas/GitHub/Controller/controller/controller.h"

#define VOLTAGEREADPIN 0
#define pinone 5
#define pintwo 6
#define SAMPLINGRATE 1000
#define RESET_INTERVAL 5000000

uint16_t adcValue = 0;
double error = 0, prevOutput = 0, output = 0, speed = 0, ref = 5, deltaT, time;
unsigned long curr, prev, prevReset;
unsigned char normalOperation = 1;

void setup()
{
    Serial.begin(9600);
    Serial.println("Tempo,Saida,Erro,Esforco");
}

void loop()
{
    curr = micros();
    if (curr - prev >= SAMPLINGRATE) // run at fixed sampling rate
    {
        adcValue = analogRead(VOLTAGEREADPIN);

        // update previous and current values
        prevOutput = output;
        output = (double)adcValue / 1023 * 5;
        time = (double)curr / 1e6;
        deltaT = (double)(curr - prev) / 1e6;
        speed = (output - prevOutput) / deltaT;

        hBridgeWrite(pinone, pintwo, ref * normalOperation);
        Serial.println(String(time, 6) + "," + String(speed, 6) + ",0,0");
        prev = micros();
    }
    if (curr - prevReset >= RESET_INTERVAL) // stops motor every few seconds
    {
        normalOperation = 0;
        if (curr - prevReset >= 1.5 * RESET_INTERVAL) // if enough time has passed, start normal operation again
        {
            normalOperation = 1;
            prevReset = micros();
        }
    }
}
