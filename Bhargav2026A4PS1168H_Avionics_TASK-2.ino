#include <LiquidCrystal.h> // for lcd

// PIN
LiquidCrystal lcd(12, 11, 5, 4, 3, 2);   // RS, E, D4, D5, D6, D7

const int pingPin    = 9;    // ultrasonic sensor
const int lightPin   = A0;   // photoresistor
const int buttonPin  = 6;    // switch-button
const int ledPin     = 7;    // led
const int buzzerPin  = 8;    // buzzer

// Setting up Threshold
const int  LIGHT_THRESHOLD    = 512;   // half brightness
const long DISTANCE_THRESHOLD = 100;   // cm
const unsigned long WRECK_TIME_MS = 5000;  // 5 seconds

// Setting up States
enum State { OPEN_SEA, ANCHOR_DROPPED, STORM, CHARYBDIS, WRECKED };
State currentState  = OPEN_SEA;
State previousState = WRECKED;   // deliberately wrong so the LCD prints once at startup just for it to change to opensea, anchor drop

unsigned long dangerStartTime = 0;   // time starts when we eneter STORM or CHARYBDIS

// LED blink time
unsigned long lastBlinkTime = 0;
bool ledOn = false;
const unsigned long BLINK_INTERVAL_MS = 300;

// button debounce and time
bool lastRawReading   = LOW;
bool debouncedState   = LOW;
unsigned long lastDebounceTime = 0;
const unsigned long DEBOUNCE_DELAY_MS = 50;

// Ultrasonic-sensor
long readDistanceCM() {
  pinMode(pingPin, OUTPUT);
  digitalWrite(pingPin, LOW);
  delayMicroseconds(2);
  digitalWrite(pingPin, HIGH);
  delayMicroseconds(5);
  digitalWrite(pingPin, LOW);

  pinMode(pingPin, INPUT);
  long duration = pulseIn(pingPin, HIGH, 30000UL);
  if (duration == 0) return 999;
  return duration / 29 / 2;
}

// Button
bool buttonWasPressed() {
  bool reading = digitalRead(buttonPin);
  bool pressedEvent = false;

  if (reading != lastRawReading) {
    lastDebounceTime = millis();
  }

  if ((millis() - lastDebounceTime) > DEBOUNCE_DELAY_MS) {
    if (reading != debouncedState) {
      debouncedState = reading;
      if (debouncedState == LOW) {
        pressedEvent = false;
      }
      if (debouncedState == HIGH) {
        pressedEvent = true;
      }
    }
  }

  lastRawReading = reading;
  return pressedEvent;
}

// LCD 
void updateLCDIfChanged() {
  if (currentState == previousState) return;

  lcd.clear();
  lcd.setCursor(0, 0);

  switch (currentState) {
    case OPEN_SEA:       
      lcd.print("OPEN SEA");       
        break;
    case ANCHOR_DROPPED: 
      lcd.print("ANCHOR DROPPED"); 
        break;
    case STORM:          
      lcd.print("STORM");         
        break;
    case CHARYBDIS:      
      lcd.print("CHARYBDIS");      
        break;
    case WRECKED:        
      lcd.print("WRECKED");        
        break;
  }

  previousState = currentState;
}

void setup() {

  pinMode(buttonPin, INPUT);
  pinMode(ledPin, OUTPUT);
  pinMode(buzzerPin, OUTPUT);

  lcd.begin(16, 2);
  updateLCDIfChanged();
}

// Setting up the loop
void loop() {

  bool pressed = buttonWasPressed();
  int  lightVal = analogRead(lightPin);
  long distance = readDistanceCM();

  bool stormCondition = lightVal < LIGHT_THRESHOLD;
  bool charybdisCondition = distance < DISTANCE_THRESHOLD;
  
  // States of ship
  switch (currentState) {

    case OPEN_SEA:
      if (pressed) {
        currentState = ANCHOR_DROPPED;
      } else if (stormCondition) {
        currentState = STORM;
        dangerStartTime = millis();
      } else if (charybdisCondition) {
        currentState = CHARYBDIS;
        dangerStartTime = millis();
      }
      break;

    case ANCHOR_DROPPED:
      if (pressed) {
        currentState = OPEN_SEA;
      }
      break;

    case STORM:
      if (pressed) {
        currentState = ANCHOR_DROPPED;
      } else if (!stormCondition) {
        currentState = OPEN_SEA;
      } else if (millis() - dangerStartTime >= WRECK_TIME_MS) {
        currentState = WRECKED;
      }
      break;

    case CHARYBDIS:
      if (pressed) {
        currentState = ANCHOR_DROPPED;
      } else if (!charybdisCondition) {
        currentState = OPEN_SEA;
      } else if (millis() - dangerStartTime >= WRECK_TIME_MS) {
        currentState = WRECKED;
      }
      break;

    case WRECKED:
      break;
  }

  // LED blinking
  if (currentState == STORM) {
    if (millis() - lastBlinkTime >= BLINK_INTERVAL_MS) {
      lastBlinkTime = millis();
      ledOn = !ledOn;
      digitalWrite(ledPin, ledOn ? HIGH : LOW);
    }
  } else {
    digitalWrite(ledPin, LOW);
  }

  // Buzzer during CHARYBDIS
  digitalWrite(buzzerPin, (currentState == CHARYBDIS) ? HIGH : LOW);

  updateLCDIfChanged();
}