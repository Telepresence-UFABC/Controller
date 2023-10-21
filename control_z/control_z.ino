#include "/home/nikolas/Documents/GitHub/Controller/controller/controller.h"

#define VOLTAGEREADPIN 0
#define VOLTAGEWRITEPIN 3
#define SAMPLINGRATE 1000000

Measure *err = createMeasure();
Measure *u = createMeasure();

double ref = 1.0, systemOutput = 0.0, intervalSeconds = 0.0;
unsigned long prev = micros(), curr = micros();
char outputString[100];

void setup()
{
    Serial.begin(115200);
};

void loop()
{
    curr = micros();
    if (curr - prev >= SAMPLINGRATE)
    {
        intervalSeconds = (curr - prev) / 1e6;
        double systemOutput = adc2real(analogRead(VOLTAGEREADPIN));

        // update previous and current values
        err->prev = err->curr;
        err->curr = ref - systemOutput;

        u->prev = u->curr;
        u->curr = 0.9656449798564605 * u->prev + 0.069255968776331 * err->curr - 0.06759113027113339 * err->prev; // numerically solve recurrence equation

        analogWrite(VOLTAGEWRITEPIN, real2pwm(u->curr));

        sprintf(outputString, "Current error: %f\nControl value: %f\n----------------------------\n", err->curr, u->curr);
        Serial.print(outputString);
        prev = micros();
    }
};