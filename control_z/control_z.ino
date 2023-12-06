#include "/home/nikolas/Documents/GitHub/Controller/controller/controller.h"

#define VOLTAGEREADPIN 0
#define pinone 5
#define pintwo 6
#define SAMPLINGRATE 5000

Measure *err = createMeasure();
Measure *u = createMeasure();

uint16_t adcValue = 0;
double output, time, ref = 3.5;
unsigned long curr, prev;
char outputString[100];

void setup()
{
    Serial.begin(9600);
};

void loop()
{
    curr = micros();
    if (curr - prev >= SAMPLINGRATE)
    {
        time = (curr - prev) / 1e6;
        adcValue = analogRead(VOLTAGEREADPIN);
        output = (double)adcValue/1023*5;

        // update previous and current values
        err->prev = err->curr;
        err->curr = ref - output;
        err->curr = err->curr > 0 ? err->curr + 1 : err->curr - 1; // motor starts to run at about 1V

        u->prev = u->curr;
        u->curr = 0.13403841905010236 * u->prev + 4499.797360001363 * err->curr - 3339.5093253347313 * err->prev; // numerically solve recurrence equation

        hBridgeWrite(pinone, pintwo, u->curr);

        Serial.println(err->curr > 0 ? err->curr - 1 : err->curr + 1);
        prev = micros();
    }
};