#include <Servo.h>
#include "Stepper.h"
#define NUM_REF_RESISTORS 8
#define NUM_SELECT_PINS   3
#define MAX_ANALOG_VALUE  1023
#define SWITCH_RESISTANCE 20

// Note that the 5V CD74HC4051 8:1 Mutiplexer routes signals from X0, x1, ...x7 to X.
// X0 is the least significant (ABC=0b000), while X7 is most significant (ABC=0b111)
// Reference Resistor values      x0    x1   x2     x3     x4       x5       x6       x7
float rRef[NUM_REF_RESISTORS] = {10, 47, 100, 470, 1000, 10000, 100000, 1000000};
// Multiplexer select pins              0  1  2
const byte rSelPins[NUM_SELECT_PINS] = {2, 3, 4};
const byte enableMux = 6; // 1 = no connection, 0 = one of eight signals connected
float scl_factor; // used to account for inaccuracies in resistance calculation due to loading and other factors
float measuredRes_new;
float measuredRes_old = 5000;
int angle;
int resDetected = 0; // look for repeated consistent value for resistance detection
float givenRes[8] = {10, 50, 100, 1000, 5000, 24000, 80000, 150000};
int boxNumber;

const int stepsPerRev = 2048;
Stepper conveyor = Stepper(stepsPerRev, 8,9,10,11);

class Spinner
{
  public:
  int currPos;
  Servo servo;

  void begin(byte pin)
  {
    servo.attach(pin);
  }

  void move_to(int pos)
  {
    
    int nextPos = 0;
    for (int i = 1; i < 100; i++){
      //Serial.println(i);
      nextPos = currPos + i*(pos - currPos)/100;
      //Serial.println(nextPos);
      servo.write((nextPos));
      delay(30);
      //Serial.println("hi");
    }
    currPos = pos;
  }

};

Spinner spinner;
Servo flipper;

void setup()
{
  Serial.begin(9600);
  pinMode(enableMux, OUTPUT);
  digitalWrite(enableMux, HIGH);      // disable all switches
  
  for (int i = 0; i < NUM_SELECT_PINS; i++)
  {
    pinMode(rSelPins[i], OUTPUT);     // Mux select pins configured as outputs
    digitalWrite(rSelPins[i], HIGH); 
  }
  spinner.begin(6);
  flipper.attach(7);
  flipper.write(100);
  conveyor.setSpeed(5);
  spinner.move_to(0);
}

String data;

void loop()
{
  spinner.move_to(0);
  if(Serial.available() > 0){
    data = Serial.readStringUntil('\n');
    //Serial.println(data);
  }

  flipper.write(100);
  if (data.charAt(0) == 'S'){
    spinner.move_to(0);
    // If 10 resistor measurements are consistent, resistance value has been detected
    //spinner.move_to(70);
    while (resDetected < 1) {
      //conveyor.setSpeed(500);
      conveyor.step(500); // run conveyor belt

      measuredRes_new = measureResistance();
      if (fabs(1 - measuredRes_new/measuredRes_old) < .1) {
        resDetected++;
      } else {
        resDetected = 0;
      }
      measuredRes_old = measuredRes_new;
      Serial.println("Resistor not found");
      if(Serial.available() > 0){
        data = Serial.readStringUntil('\n');
        if(data.charAt(0) != 'S'){
          break;
        }
      }
    }
    //Serial.println("resistor found!!");


    // send resistor value to GUI
    Serial.println(measuredRes_new);

    while( Serial.available() == 0){}
    boxNumber = Serial.parseInt();
    //boxNumber = checkResistorValue(givenRes, measuredRes_new); // boxNumber is received from GUI
    //Serial.println(boxNumber);

    angle = mapNumbertoAngle(boxNumber) - angle;
    //Serial.println(angle);

    // feed angle into servo code, power servo
    spinner.move_to(abs(angle));
    delay(3000);

    // trigger flipping mechanism
    if(angle < 0)
    {
      flipper.write(180);
    } else
    {
      flipper.write(0);
    }
    delay(2000);
    flipper.write(100);

    resDetected = 0;
    //Serial.println(data);
  }
}

// Function to check if measured resistor is within 10% of any given resistor values
int checkResistorValue(float givenRes[], int measuredRes) {
    // Loop through each of the 8 given resistor values
    float err;
    for (int i = 0; i < 8; i++) {
        
        // Calculate 10% of the given resistor value
        err = givenRes[i] * 0.10;
        
        // Check if the measured resistor is within 10% tolerance of the given resistor value
        if (measuredRes >= (givenRes[i] - err) && measuredRes <= (givenRes[i] + err)) {
            return i;  // If the measured resistor is within reasonable range of the given resistor, return that resistor's box number
        }
    }
    return 8;  // If no match was found, return trash bin
}

int mapNumbertoAngle(int boxNumber) {
  switch(boxNumber) {
        case 0:
            angle = 0;
            break;
        case 1:
            angle = 40;
            break;
        case 2:
            angle = 80;
            break;
        case 3:
            angle = 120;
            break;
        case 4:
            angle = 160;
            break;
        case 5:
            angle = -20;
            break;
        case 6:
            angle = -60;
            break;
        case 7:
            angle = -100;
            break;
        case 8:
            angle = -140;
            break;
}

}

// Precision auto-ranging Ohmmeter using the Arduino to measure resistances
// in the range of 0 Ohms to 1 GOhms.
//
// Parts (refer to the schematic):
//    Arduino Pro Mini, MAX4617CPE 8:1 Analog Multiplexer, eight 1% tolerance 
//    reference resistors, SSD 1306 OLED display, 220uF 16V capacitor.
//
// The design and operation is described in detail in a separate document, 
// which also contains the full schematic diagram.
// 
// By Steve S. (C) Feb, 2021
//
// Current code is designed to use a SSD 1306 OLED display (128x64 resolution)
// ---------------------------------------------------------------------------
 
float measureResistance() {
  int cOut;
  float delta, deltaBest1 = MAX_ANALOG_VALUE, deltaBest2 = MAX_ANALOG_VALUE;
  float rBest1 = -1, rBest2 = -1, rR, rX; 
  float rfBest1 = -1, rfBest2 = -1;

  for (byte count = 0; count < NUM_REF_RESISTORS; count++)
  {
    // Set the Mux select pins to switch in one Rref at a time.
    // count=0: Rref0 (10 ohms), count=1: Rref1 (47 ohms), etc...
    digitalWrite(rSelPins[0], count & 1); // C: least significant bit
    digitalWrite(rSelPins[1], count & 2); // B:
    digitalWrite(rSelPins[2], count & 4); // A: most significant bit
    
    digitalWrite(enableMux, LOW);       // enable the selected reference resistor
  
    delay(50*(count+1)); // delay 50ms for Rref0, 100ms for Ref1, etc...

    cOut = analogRead(A5);              // convert analog voltage Vx to a digital value
    // Serial.print ("cOut: ");Serial.println(cOut);

    digitalWrite(enableMux, HIGH);      // disable the selected reference resistor
    delay(50*(NUM_REF_RESISTORS - count));   // delay 400ms for Rref0, 350ms for Ref1, etc...
    // Work only with valid digitized values
    if (cOut < MAX_ANALOG_VALUE)
    {
      // Identify the Rref value being used and compute Rx based on formula #2.
      // Note how Mux's internal switch resistance is added to Rref. 
      rR = rRef[count] + SWITCH_RESISTANCE; 
      // Serial.print("rR: ");Serial.println(rR);
      rX = (rR * cOut) / (MAX_ANALOG_VALUE - cOut); // computing Rx from ratio
      delta = (MAX_ANALOG_VALUE / 2.0 - cOut); // checking to see which rRef value is best
      if (fabs(delta) < fabs(deltaBest1))
      {
        deltaBest2 = deltaBest1;
        rBest2 = rBest1;
        rfBest2 = rfBest1;
        deltaBest1 = delta;
        rBest1 = rX;
        rfBest1 = rR;
      }
      else if (fabs(deltaBest2) > fabs(delta))
      {
        deltaBest2 = delta;
        rBest2 = rX;
        rfBest2 = rR;
      }
    }
  }
  // Make sure there are at least two good samples to work with
  if (rBest1 >= 0 && rBest2 >= 0)
  {
    // Check to see if need to interpolate between the two data points.
    // Refer to the documentation for details regarding this.
    if (deltaBest1 * deltaBest2 < 0)
    {
      rX = rBest1 - deltaBest1 * (rBest2 - rBest1) / (deltaBest2 - deltaBest1); // Yes
    }
    else
    {
      rX = rBest1;  // No. Just use the best value
    }
    // Convert the scaled float result to string and extract the units
    // unit = ScaleToMetricUnits(&rX, fStr);
  } else { // if there aren't two good samples, r value is > 100kOhms
    rX = rBest1;
  }

  // Account for measurement inaccuracies with experimentally determined scaling values
  if (rX < 140) {
    scl_factor = 1/(1 + (rX - 10)*0.004);
  } else if (rX < 370) {
    scl_factor = 0.658 + ((rX - 140)*0.004);
    // Serial.println(scl_factor);
  } else if (rX < 1000) {
    scl_factor = 1.2;
    // Serial.println(scl_factor);
  } else if (rX < 30000) {
    scl_factor = 1.2 - ((rX - 1000)*0.00001);
    // Serial.println(scl_factor);
  } else if (rX < 50000) {
    scl_factor = 0.758 + ((rX - 30000)*0.00002);
    // Serial.println(scl_factor);
  } else {
    scl_factor = 1;
  }

  rX = rX * (scl_factor);
  //Serial.println(rX);
  return rX;
  
  Serial.print("rfBest1: ");Serial.println(rfBest1);
  delay(250);
}