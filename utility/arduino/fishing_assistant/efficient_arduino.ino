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

int bezierPoint(int start, int c1, int c2, int end, float t) {
  return (int) (pow(1 - t, 3) * start + 3 * t * pow(1 - t, 2) * c1 + 3 * pow(t, 2) * (1 - t) * c2 + pow(t, 3) * end);
}

void move_mouse(String params) {
  // Split the params string into its different parts
  int currentXIndex = params.indexOf(',');
  int currentYIndex = params.indexOf(',', currentXIndex + 1);
  int nextXIndex = params.indexOf(',', currentYIndex + 1);
  int nextYIndex = params.indexOf(',', nextXIndex + 1);

  int currentX = params.substring(0, currentXIndex).toInt();
  int currentY = params.substring(currentXIndex + 1, currentYIndex).toInt();
  int targetX = params.substring(currentYIndex + 1, nextXIndex).toInt();
  int targetY = params.substring(nextXIndex + 1, nextYIndex).toInt();

  // Generate random control points for the Bezier curve
  int c1x = random(currentX, targetX);
  int c1y = random(currentY, targetY);
  int c2x = random(currentX, targetX);
  int c2y = random(currentY, targetY);

  // Calculate the step size for the curve
  float stepSize = 1.0 / max(abs(targetX - currentX), abs(targetY - currentY));

  // Move the mouse along the curve
  for (float t = 0; t <= 1.0; t += stepSize) {
    int x = bezierPoint(currentX, c1x, c2x, targetX, t);
    int y = bezierPoint(currentY, c1y, c2y, targetY, t);

    // Move the mouse in increments of at most 127 units until it reaches the target position
    while (currentX != x || currentY != y) {
      int dx = min(127, x - currentX);
      int dy = min(127, y - currentY);
      Mouse.move(dx, dy, 0);
      currentX += dx;
      currentY += dy;
    }
  }
  Serial.println("Finished");
}