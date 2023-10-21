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

int real2pwm(double real)
{
    return (int)255 / 5 * max(0.0, min(real, 5.0));
}

double adc2real(int pwm)
{
    return (double)5.0 / 1023 * pwm;
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