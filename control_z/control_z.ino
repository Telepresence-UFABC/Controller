#include "/home/nikolas/GitHub/Controller/controller/controller.h"

#define VOLTAGEREADPIN 0
#define pinone 5
#define pintwo 6
#define SAMPLINGRATE 5000

Measure *err = createMeasure();
Measure *u = createMeasure();

uint16_t adcValue = 0;
double output, time, ref = 1;
unsigned long curr, prev;
char outputString[100];

void setup()
{
    Serial.begin(9600);
    Serial.println("Erro,Esforco");
};

void loop()
{
    curr = micros();
    if (curr - prev >= SAMPLINGRATE)
    {
        time = (double)(curr - prev) / 1e6;
        adcValue = analogRead(VOLTAGEREADPIN);
        output = (double)adcValue/1023*5;

        // update previous and current values
        err->prev = err->curr;
        err->curr = ref - output;
        err->curr = err->curr;

        u->prev = u->curr;
        u->curr = 0.904754387023486 * u->prev + 16.913131432044782 * err->curr - 15.675594439833445 * err->prev; // numerically solve recurrence equation

        hBridgeWrite(pinone, pintwo, u->curr);

        Serial.println(String(err->curr, 6) + "," + String(u->curr, 6));
        prev = micros();
    }
};