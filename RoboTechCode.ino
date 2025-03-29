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
 
// #include <U8glib.h>
#define NUM_REF_RESISTORS 8
#define NUM_SELECT_PINS   3
#define MAX_ANALOG_VALUE  1023
#define SWITCH_RESISTANCE 20

// Note that the MAX4617 8:1 Mutiplexer routes signals from X0, x1, ...x7 to X.
// It uses 3 select lines A, B and C to choose one of the signals.
// X0 is the least significant (ABC=0b000), while X7 is most significant (ABC=0b111)
// Reference Resistor values      x0    x1   x2     x3     x4       x5       x6       x7
float rRef[NUM_REF_RESISTORS] = {10, 47, 100, 470, 1000, 10000, 100000, 1000000};
// Multiplexer select pins              A  B  C
const byte rSelPins[NUM_SELECT_PINS] = {2, 3, 4};
const byte enableMux = 6; // 1 = no connection, 0 = one of eight signals connected
float scl_factor;
// int screenWidth, screenHeight;
// // Enable the display type to be used. We use SPI for now, but can also use I2C.
// U8GLIB_SSD1306_128X64 u8g(13, 11, 10, 9, 12); // SW SPI: SCK/D0 = 13, MOSI/D1 = 11, CS = 10, A0/DC = 9, RESET = 12
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

  // select the highest Rref
  // digitalWrite(rSelPins[0], HIGH);  
  // digitalWrite(rSelPins[1], LOW);  
  // digitalWrite(rSelPins[2], HIGH);  

  // screenWidth = u8g.getWidth();
  // screenHeight = u8g.getHeight();
  // DisplayIntroScreen();

  // Serial.println("\nStarting ArduinOhmmeter...");
}
// This function scales the resistor value, so that it
// can be expressed in Ohms, KOhms, MOhms or GOhms.
// It then ensures that 3 digits of precision are 
// present in the final result.
// char ScaleToMetricUnits(float *prVal, char fStr[])
// {
//   char unit;
//   if (*prVal < 1000)
//   {
//     unit = ' ';
//   }
//   else if (*prVal >= 1000 && *prVal < 1000000)
//   {
//     *prVal /= 1000;
//     unit = 'K';
//   }
//   else if (*prVal >= 1000000 && *prVal < 1000000000)
//   {
//     *prVal /= 1000000;
//     unit = 'M';
//   }
//   else
//   {
//     *prVal /= 1000000000;
//     unit = 'G';
//   }
//   // Cycle the decimal number in prVal until its whole number is 0.
//   // Note that counter 'k' is decremented from 2 to 0 (inclusive),
//   // which gives us the 3-digit precision we're looking for.
//   for (int k=2, s=10; k >= 0; k--, s*=10)
//   {
//     if ((int)(*prVal) / s == 0)
//     {
//       dtostrf(*prVal, 4, k, fStr); // convert the float result to a string
//       break;
//     }
//   }
//   return unit;
// }
// Central routine to display the image on the SSD 1306.
// 'xTop' and 'xBot' are the x-coordinates of the two words that can
// be moved horizontally (during intro) or kept in place (when measuring).
// 'unit' is a 1-byte character for unit: ' ', 'K', 'M' or 'G'. 0 if no reading.
// 'fStr' is the string representation of the 3-digit decimal value to display.
// void DisplayResultsOnLEDScreen(int xTop, int xBot, char unit, char fStr[])
// {
//   u8g.firstPage();
//   do {
//       char myStr[8];
//       u8g.setFont(u8g_font_profont12r);     // use small font for letters
//       u8g.drawStr(xTop, 9, "ArduinO");
//       u8g.drawStr(xBot, 16, "Ohmmeter");
//       u8g.drawRFrame(0, 16, screenWidth-1, screenHeight-16, 3);
//       u8g.drawLine(0, 0, 0, 15);
//       u8g.drawLine(90, 0, 90, 15);
//       u8g.drawLine(screenWidth-1, 0, screenWidth-1, 15);
//       u8g.setFont(u8g_font_fur30r);         // switch to large font for numbers
//       if (unit != 0)
//       {
//         sprintf(myStr, "%6s", fStr);
//         u8g.drawStr(0, 56, myStr);
//         sprintf(myStr, "%c%c", unit, 'W');  // 'W' stands for Greek 'Omega'
//         u8g.setFont(u8g_font_symb14r);      // switch to symbol font for unit
//         u8g.drawStr(95, 16, myStr);
//       }
//       else
//       {
//         strcpy(myStr, "- - -");
//         u8g.drawStr((screenWidth-u8g.getStrPixelWidth(myStr))/2, 48, myStr);
//       }
//    } while (u8g.nextPage());
// }
// // Routine to display the animated introductory screen
// void DisplayIntroScreen(void)
// {
//   for (int xTop = 40, xBot = 4; xTop >= 4; xTop--, xBot++)
//   {
//     DisplayResultsOnLEDScreen(xTop, xBot, 0, 0);
//     if (xTop == 40) delay(500);
//   }
// }


void loop()
{
  int cOut;
  float delta, deltaBest1 = MAX_ANALOG_VALUE, deltaBest2 = MAX_ANALOG_VALUE;
  float rBest1 = -1, rBest2 = -1, rR, rX; 
  float rfBest1 = -1, rfBest2 = -1;
  // char unit = 0, fStr[16];
  for (byte count = 0; count < NUM_REF_RESISTORS; count++)
  {
    // Set the Mux select pins to switch in one Rref at a time.
    // count=0: Rref0 (49.9 ohms), count=1: Rref1 (100 ohms), etc...
    digitalWrite(rSelPins[0], count & 1); // C: least significant bit
    digitalWrite(rSelPins[1], count & 2); // B:
    digitalWrite(rSelPins[2], count & 4); // A: most significant bit
    
    digitalWrite(enableMux, LOW);       // enable the selected reference resistor
    // if (cOut > 880) {
    //     delay(100*(count+1));
    // } else {
    //   delay(count+1);
    // }
    delay(50*(count+1));
    
                     // delay 1ms for Rref0, 2ms for Ref1, etc...
    cOut = analogRead(A5);              // convert analog voltage Vx to a digital value
    Serial.print ("cOut: ");Serial.println(cOut);
    // Serial.println(cOut);
    digitalWrite(enableMux, HIGH);      // disable the selected reference resistor
    delay(50*(NUM_REF_RESISTORS - count));   // delay 8ms for Rref0, 7ms for Ref1, etc...
    // Work only with valid digitized values
    if (cOut < MAX_ANALOG_VALUE)
    {
      // Identify the Rref value being used and compute Rx based on formula #2.
      // Note how Mux's internal switch resistance is added to Rref. 
      rR = rRef[count] + SWITCH_RESISTANCE; 
      Serial.print("rR: ");Serial.println(rR);
      rX = (rR * cOut) / (MAX_ANALOG_VALUE - cOut); // computing Rx from ratio
      // Serial.print("rX(");Serial.print(count);Serial.print(") ");Serial.println(rX);
      // Compute the delta and track the top two best delta and Rx values
      // if (cOut > 880 && count == 7) {
      //   rfBest1 = 100000;
        
      // }
      // if (cOut > 880 && count == 7) {
      //   // rfBest1 = 100000;
      //   rX = (100000 * cOut) / (MAX_ANALOG_VALUE - cOut);
      //   Serial.println(rX);
      // } else {
      delta = (MAX_ANALOG_VALUE / 2.0 - cOut); // checking to see which rRef value is best
      if (fabs(delta) < fabs(deltaBest1))
      {
        deltaBest2 = deltaBest1;
        rBest2 = rBest1;
        rfBest2 = rfBest1;
        deltaBest1 = delta;
        rBest1 = rX;
        rfBest1 = rR;
        // Serial.println(rfBest1);
        // Serial.println(rfBest2);
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
  } else {
    rX = rBest1;
  }

  if (rX > 10 && rX < 140) {
    scl_factor = 1/(1 + (rX - 10)*0.004);
  } else if (rX < 370) {
    scl_factor = (1/(1 + (140 - 10)*0.004)) + ((rX - 140)*0.003);
    Serial.println(scl_factor);
  } else if (rX < 1000) {
    scl_factor = 1.2;
    Serial.println(scl_factor);
  } else if (rX < 30000) {
    scl_factor = 1.2 - ((rX - 1000)*0.00001);
    Serial.println(scl_factor);
  } else if (rX < 50000) {
    scl_factor = 0.758 + ((rX - 30000)*0.00002);
    Serial.println(scl_factor);
  } else {
    scl_factor = 1;
  }

  rX = rX * (scl_factor);
  Serial.println(rX);
  Serial.print("rfBest1: ");Serial.println(rfBest1);
  delay(250);
}
