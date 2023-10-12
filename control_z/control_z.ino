#define VOLTAGEREADPIN 0
#define VOLTAGEWRITEPIN 3

double ref = 1.0, systemOutput = 0.0, uN_0 = 0.0, uN_1 = 0.0, errN_0 = 0.0, errN_1 = 0.0, errN_2 = 0.0;
unsigned int pwmValue = 0;

void setup()
{
    Serial.begin(9600);
};

void loop()
{
    double systemOutput = pwm2real(analogRead(VOLTAGEREADPIN));

    errN_2 = errN_1;
    errN_1 = errN_0;
    errN_0 = ref - systemOutput;

    uN_1 = uN_0;
    uN_0 = controller(uN_1, errN_0, errN_1, errN_2);

    pwmValue = real2pwm(uN_0);

    analogWrite(VOLTAGEWRITEPIN, pwmValue);

    Serial.println("Control value: " + String(uN_0));
    Serial.println("Reference: " + String(ref));
    Serial.println("Output value: " + String(systemOutput));
};

int real2pwm(double real)
{
    return (int)255 / 5 * max(0.0, min(real, 5.0));
}

double pwm2real(int pwm)
{
    return (double)5.0 / 1023 * pwm;
}

double controller(double uN_1, double errN_0, double errN_1, double errN_2)
{
    return uN_1 + 11.85 * errN_0 - 23.32 * errN_1 + 11.48 * errN_2;
}
