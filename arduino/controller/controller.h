#ifndef CONTROLLER_H
#define CONTROLLER_H
#include <stdlib.h>

typedef struct
{
    double prev;
    double curr;
} Measure;

Measure *createMeasure()
{
    Measure *measure = (Measure *)malloc(sizeof(Measure));
    measure->prev = 0.0;
    measure->curr = 0.0;
    return measure;
}

double voltage2angle(double voltage)
{
    return (double)voltage / 5 * 300; // max angle read by potentiometer is 300°
}

double angle2voltage(double angle)
{
    return (double)angle / 300 * 5; // max voltage read by ADC is 5V
}

/*  ACT | P1 | P2
    FWD | 1 | 0
    BWD | 0 | 1
    BRK | 0 | 0
    BRK | 1 | 1
*/
void hBridgeWrite(int pinOne, int pinTwo, double value)
{
    value = constrain(value, -5, 5);

    int pwm = (int)255 / 5 * abs(value);

    // FORWARD
    if (value > 0)
    {
        analogWrite(pinOne, pwm);
        analogWrite(pinTwo, LOW);
    }
    // BACKWARD
    else if (value < 0)
    {
        analogWrite(pinOne, LOW);
        analogWrite(pinTwo, pwm);
    }
    // BRAKE
    else
    {
        analogWrite(pinOne, LOW);
        analogWrite(pinTwo, LOW);
    }
}

double derivative(Measure *value, double interval)
{
    return (value->curr - value->prev) / interval;
}

double riemannIntegral(Measure *value, double interval)
{
    return value->curr * interval;
}

double trapezoidalIntegral(Measure *value, double interval)
{
    return (value->prev + value->curr) / 2 * interval;
}

double simpsonsIntegral(Measure *value, double interval)
{
    return interval / 6 * (value->prev + 2 * (value->prev + value->curr) + value->curr); // assume f([t1-t0]/2) = (f(t1)+f(t2))/2
}

#endif