#include "/home/nikolas/Documents/GitHub/Controller/controller/controller.h"
#include <math.h>

#define VOLTAGEREADPIN 0
#define pinone 5
#define pintwo 6
#define SAMPLINGRATE 5000
#define RESET_INTERVAL 5000000
#define TOLERANCE 0.3

Measure *err = createMeasure();
Measure *u = createMeasure();

uint16_t adcValue = 0;
double output, time, ref = 1;
unsigned long curr, prev, prevReset;
bool resetting = false;

inline double control(Measure *err, Measure *u)
{
    return 0.904754387023486 * u->prev + 16.913131432044782 * err->curr - 15.675594439833445 * err->prev;
}

void setup()
{
    Serial.begin(9600);
    Serial.println("Tempo,Saida,Erro,Esforco");
};

void loop()
{
    curr = micros();
    if ((curr - prev >= SAMPLINGRATE) && !resetting)
    {
        time = (double)curr / 1e6;
        adcValue = analogRead(VOLTAGEREADPIN);
        output = (double)adcValue / 1023 * 5;

        // update previous and current values
        err->prev = err->curr;
        err->curr = ref - output;

        u->prev = u->curr;
        u->curr = control(err, u); // numerically solve recurrence equation

        hBridgeWrite(pinone, pintwo, u->curr);

        Serial.println(String(time, 6) + "," + String(output, 6) + "," + String(err->curr, 6) + "," + String(u->curr, 6));
        prev = micros();
    }
    if (curr - prevReset >= RESET_INTERVAL) // resets motor to 0 position every few seconds
    {
        resetting = true;
        adcValue = analogRead(VOLTAGEREADPIN);
        output = (double)adcValue / 1023 * 5;

        // update previous and current values while setting reference to zero
        err->prev = err->curr;
        err->curr = -output;

        u->prev = u->curr;
        u->curr = control(err, u); // numerically solve recurrence equation

        hBridgeWrite(pinone, pintwo, u->curr);
        if (abs(output) <= TOLERANCE) // check if motor is at zero position, if it is start testing again
        {
            resetting = false;
            prevReset = micros();
        }
    }
};