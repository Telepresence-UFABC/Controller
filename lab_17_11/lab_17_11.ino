#define pinone 5
#define pintwo 6
#define MAXTIME 5e3

/*  ACT | P1 | P2
    FWD | 1 | 0
    BWD | 0 | 1
    BRK | 0 | 0
    BRK | 1 | 1
*/
void hBridgeWrite(int pinOne, int pinTwo, double value)
{
    value = constrain(value, -5.0, 5.0);

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

void setup() {
  // put your setup code here, to run once:
  Serial.begin(9600);
}
double referencia = 0;
double erro = 0, tensao = 0, rampa = 0;
int leituraAdc = 0;
// y = x
long curr, prev;

void loop() {
  // put your main code here, to run repeatedly:
  leituraAdc = analogRead(0);
  tensao = (double)leituraAdc/1023.0*5.0;
  erro = rampa - tensao;
  erro = erro > 0 ? erro +1 : erro -1;
  // Serial.println("Erro: " + String(erro));
  // Serial.println("Tensao: " + String(tensao));
  // Serial.println();
  rampa = (double)(curr-prev)/1000.0;
  hBridgeWrite(pinone, pintwo, -erro);
  if(curr - prev > MAXTIME) prev = millis();
  curr = millis();
  Serial.println(rampa);
  Serial.println(tensao);
  Serial.println();
}
