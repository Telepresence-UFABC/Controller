#include "/home/nikolas/GitHub/Controller/controller/controller.h"
#include <math.h>

#define VOLTAGEREADPIN 0
#define pinone 5
#define pintwo 6
#define SAMPLINGRATE 5000
#define RESET_INTERVAL 5000000
#define TOLERANCE 0.05

Measure *err = createMeasure();
Measure *u = createMeasure();

uint16_t adcValue = 0;
double output, time, ref = 1;
unsigned long curr, prev, prevReset;
unsigned char normalOperation = 1;

inline double control(Measure *err, Measure *u)
{
    return 0.9448595965430482 * u->prev + 8.236474641898383 * err->curr - 7.812049534046017 * err->prev;
}

void setup()
{
    Serial.begin(9600);
    Serial.println("Tempo,Saida,Erro,Esforco");
};

void loop()
{
    curr = micros();
    if (curr - prev >= SAMPLINGRATE) // run at fixed sampling rate
    {
        adcValue = analogRead(VOLTAGEREADPIN);
        output = (double)adcValue / 1023 * 5;
        time = (double)curr / 1e6;

        // update previous and current values
        err->prev = err->curr;
        err->curr = ref * normalOperation - output; // ref - output if in normal operation, otherwise reference is set to 0

        u->prev = u->curr;
        u->curr = control(err, u); // numerically solve recurrence equation

        hBridgeWrite(pinone, pintwo, u->curr);
        Serial.println(String(time, 6) + "," + String(output, 6) + "," + String(err->curr, 6) + "," + String(u->curr, 6));
        prev = micros();
    }
    if (curr - prevReset >= RESET_INTERVAL) // resets motor to 0 position every few seconds
    {
        normalOperation = 0;
        if ((abs(output) <= TOLERANCE) &&  (curr-prevReset >= 1.5*RESET_INTERVAL)) // check if motor is at zero position, if it is and enough time has passed, start normal operation again
        {
            normalOperation = 1;
            prevReset = micros();
        }
    }
};