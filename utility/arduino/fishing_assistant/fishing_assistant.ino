#include <Keyboard.h>
#include <Mouse.h>

// how much serial data we expect before a newline
const unsigned int MAX_INPUT = 50;

// "reaction time" between key presses
const unsigned int LOWER_REACTION = 180;
const unsigned int UPPER_REACTION = 310;


void setup() {
  // open the serial port on arduino
  Serial.begin(9600);
  // initialize keyboard
  Keyboard.begin();
  // Initialize mouse
  Mouse.begin();
}


void loop() {
  // check for incoming serial data:
  while (Serial.available() > 0) {
    // Get available serial data
    String data = Serial.readStringUntil('ñ');
    // Strip delimiter from data string
    data = data.substring(0, data.indexOf('ñ')-1);
    // Print data string - debug
    Serial.println("Data string: " +data);

    // Process a char array of the characters received in the data string.
    process_data(data.c_str());
    // Flush buffer after processing. Might not be needed, just make sure to get fresh data after hitting delimiter.
    Serial.flush();
  }
}


// process incoming serial data
void process_data(const char* data) {
  for (int i = 0; i < MAX_INPUT; i++) {
    if (data[i] == NULL) {
      // Hit the end of our data array. Should probably check the actual length determined by null byte I think
      break;
    } else {
      // Notify console of key being typed on keyboard
      Serial.print("Typing key: ");
      Serial.print(data[i]);
      Serial.println();
      // Send keyboard input to host computer
      Keyboard.write(data[i]);
      delay(random(LOWER_REACTION, UPPER_REACTION));
    }
  }
}
