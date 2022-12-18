#include <Keyboard.h>
#include <Mouse.h>

// "reaction time" between key presses
const unsigned int LOWER_REACTION = 180;
const unsigned int UPPER_REACTION = 310;

void setup() {
  // open the serial port on arduino
  Serial.begin(115200);
  // initialize keyboard
  Keyboard.begin(KeyboardLayout_en_US);
  // Initialize mouse
  Mouse.begin();
}

void loop() {
  // check for incoming serial data:
  while (Serial.available() > 0) {
    // Get available serial data
    String data = Serial.readStringUntil('\n');
    // Split the data string into its different parts
    int eventTypeIndex = data.indexOf(',');
    String eventType = data.substring(0, eventTypeIndex);
    String params = data.substring(eventTypeIndex + 1);

    // Process the data based on the event type
    if (eventType == "move_mouse") {
      move_mouse(params);
    } else if (eventType == "click_mouse") {
      // mouse_click(params);
      Serial.println("Clicking mouse");
      Mouse.click();
      Serial.println("Finished");
    } else if (eventType == "type_string") {
      type_string(params);
    }
  }
}

void type_string(String params) {
  // Split the params string into its different parts
  int inputStringIndex = params.indexOf(',');
  String inputString = params.substring(0, inputStringIndex);

  Serial.print("Sending key: ");
  Serial.println(inputString);
  if (inputString == "enter") {
    Keyboard.press(KEY_RETURN);
    delay(51);
    Keyboard.release(KEY_RETURN);
  } else if (inputString == "esc") {
    Keyboard.press(KEY_ESC);
    delay(51);
    Keyboard.release(KEY_ESC);
  } else {
    Keyboard.print(inputString);
  }
  Serial.println("Finished");
}

void move_mouse(String params) {
  // Split the params string into its different parts
  int currentXIndex = params.indexOf(',');
  int currentYIndex = params.indexOf(',', currentXIndex + 1);
  int nextXIndex = params.indexOf(',', currentYIndex + 1);
  int nextYIndex = params.indexOf(',', nextXIndex + 1);

  int currentX = params.substring(0, currentXIndex).toInt();
  int currentY = params.substring(currentXIndex + 1, currentYIndex).toInt();
  int nextX = params.substring(currentYIndex + 1, nextXIndex).toInt();
  int nextY = params.substring(nextXIndex + 1, nextYIndex).toInt();

  Serial.print("Moving mouse from: ");
  Serial.print(currentX);
  Serial.print(" ");
  Serial.print(currentY);
  Serial.print(" to ");
  Serial.print(nextX);
  Serial.print(" ");
  Serial.println(nextY);

  // Calculate the distance to move in the x and y directions
  int deltaX = nextX - currentX;
  int deltaY = nextY - currentY;

  // Break the movement into smaller steps, if necessary, to stay within the limits of Mouse.move()
  while (deltaX != 0 || deltaY != 0) {
    int stepX = deltaX;
    int stepY = deltaY;

    // Won't work correctly if giving the max values. probably...
    if (abs(stepX) > 127) {
      stepX = 127 * (stepX > 0 ? 1 : -1);
    }
    if (abs(stepY) > 127) {
      stepY = 127 * (stepY > 0 ? 1 : -1);
    }

    // Make the mouse move
    Mouse.move(stepX, stepY);

    // Decrement the distance to move by the amount we just moved
    deltaX -= stepX;
    deltaY -= stepY;
  }
  Serial.println("Finished");
}
