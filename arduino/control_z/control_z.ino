#include "/home/nikolas/Documents/GitHub/Controller/arduino/controller/controller.h"
#include <math.h>

#define VOLTAGE_READ_PIN 0
#define PIN_ONE 5
#define PIN_TWO 6
#define SAMPLING_INTERVAL 5000
#define RESET_INTERVAL 2000000
#define TOLERANCE 0.05

Measure *err = createMeasure();
Measure *u = createMeasure();

uint16_t adcValue = 0;
double output, time, ref = 1;
unsigned long curr, prev, prevReset;
unsigned char normalOperation = 1;

inline double control(Measure *err, Measure *u)
{
    return 0.953720311449073 * u->prev + 6.093249363038537 * err->curr - 5.851599403259743 * err->prev;
}

void setup()
{
    Serial.begin(9600);
    Serial.println("Tempo,Saida,Erro,Esforco");
};

void loop()
{
    curr = micros();
    if (curr - prev >= SAMPLING_INTERVAL) // run at fixed sampling rate
    {
        adcValue = analogRead(VOLTAGE_READ_PIN);
        output = (double)adcValue / 1023 * 5;
        time = (double)curr / 1e6;

        // update previous and current values
        err->prev = err->curr;
        err->curr = ref * normalOperation - output; // ref - output if in normal operation, otherwise reference is set to 0

        u->prev = u->curr;
        u->curr = control(err, u); // numerically solve recurrence equation

        hBridgeWrite(PIN_ONE, PIN_TWO, u->curr);
        Serial.println(String(time, 6) + "," + String(output, 6) + "," + String(err->curr, 6) + "," + String(u->curr, 6));
        prev = micros();
    }
    if (curr - prevReset >= RESET_INTERVAL) // resets motor to 0 position every few seconds
    {
        normalOperation = 0;
        if ((abs(output) <= TOLERANCE) && (curr - prevReset >= 1.5 * RESET_INTERVAL)) // check if motor is at zero position, if it is and enough time has passed, start normal operation again
        {
            normalOperation = 1;
            prevReset = micros();
        }
    }
};