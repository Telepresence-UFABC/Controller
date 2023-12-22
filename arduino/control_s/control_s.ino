#include "/home/nikolas/Documents/GitHub/Controller/arduino/controller/controller.h"

#define VOLTAGEREADPIN 0
#define VOLTAGEWRITEPIN 3
#define PIN_ONE 5
#define PIN_TWO 6
#define SAMPLING_INTERVAL 1000000

Measure *err = createMeasure();
Measure *errDot = createMeasure();
Measure *errDotDot = createMeasure();
Measure *u = createMeasure();
Measure *uDot = createMeasure();

uint16_t adcValue = 0;
double ref = 1, output = 0, time = 0, deltaT = 0;
unsigned long prev = micros(), curr = micros();

void setup()
{
    Serial.begin(115200);
};

void loop()
{
    curr = micros();
    if (curr - prev >= SAMPLING_INTERVAL)
    {
        adcValue = analogRead(VOLTAGEREADPIN);
        output = (double)adcValue / 1023 * 5;
        time = (double)curr / 1e6;

        deltaT = (curr - prev) / 1e6;

        // update previous and current values
        err->prev = err->curr;
        err->curr = ref - output;

        errDot->prev = errDot->curr;
        errDot->curr = derivative(err, deltaT);

        errDotDot->prev = errDotDot->curr;
        errDotDot->curr = derivative(errDot, deltaT);

        uDot->prev = uDot->curr;
        uDot->curr = -34.95902799659847 * u->curr + 1.6941086242955898 * err->curr + 0.06925596877633099 * errDot->curr; // numerically solve differential equation

        u->prev = u->curr;
        u->curr += riemannIntegral(uDot, deltaT);

        hBridgeWrite(PIN_ONE, PIN_TWO, u->curr);

        Serial.println(String(time, 6) + "," + String(output, 6) + "," + String(err->curr, 6) + "," + String(u->curr, 6));
        prev = micros();
    }
};