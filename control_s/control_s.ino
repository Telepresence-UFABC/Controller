#include "/home/nikolas/Documents/GitHub/Controller/controller/controller.h"

#define VOLTAGEREADPIN 0
#define VOLTAGEWRITEPIN 3

Measure *err_0 = createMeasure(0.0, 0.0);
Measure *err_1 = createMeasure(0.0, 0.0);
Measure *err_2 = createMeasure(0.0, 0.0);
Measure *u_0 = createMeasure(0.0, 0.0);
Measure *u_1 = createMeasure(0.0, 0.0);
Measure *u_2 = createMeasure(0.0, 0.0);

double ref = 1.0, systemOutput = 0.0, intervalSeconds = 0;
unsigned int pwmValue = 0;
unsigned long prev = micros();
char outputString[50];

void setup()
{
    Serial.begin(9600);
};

void loop()
{
    intervalSeconds = (micros() - prev) / 1e6;
    prev = micros();

    systemOutput = pwm2real(analogRead(VOLTAGEREADPIN));

    err_0->curr = ref - systemOutput;
    err_1->curr = derivative(err_0, intervalSeconds);
    err_2->curr = derivative(err_1, intervalSeconds);

    u_1->curr = -34.95902799659847 * u_0->curr + 1.6941086242955898 * err_0->curr + 0.06925596877633099 * err_1->curr; // numerically solve differential equation
    u_0->curr += riemannIntegral(u_1, intervalSeconds);

    analogWrite(VOLTAGEWRITEPIN, real2pwm(u_0->curr));

    sprintf(outputString, "Reference: %.2lf\nControl value: %.2lf\nOutput value: %.2lf\n", ref, u_0->curr, systemOutput);
    Serial.print(outputString);
};

int real2pwm(double real)
{
    return (int)255 / 5 * max(0.0, min(real, 5.0));
}

double pwm2real(int pwm)
{
    return (double)5.0 / 1023 * pwm;
}
