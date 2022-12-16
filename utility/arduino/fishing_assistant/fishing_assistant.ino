#include <Keyboard.h>
#include <Mouse.h>
#include <ArduinoJson.h>

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
    String data = Serial.readStringUntil('\n');
    // Deserialize data to json
    StaticJsonDocument<192> doc;
    DeserializationError error = deserializeJson(doc, data);
    // Check if we failed to deserialize the data
    if (error) {
      Serial.print(F("deserializeJson() failed: "));
      Serial.println(error.f_str());
      return;
    }
    // Process json data
    process_json(doc);
    // Flush buffer after processing. Might not be needed, just make sure to get fresh data after hitting delimiter.
    Serial.flush();
  }
}


void process_json(StaticJsonDocument<192> d) {
  const char* event_type = d["event_type"];
  // JsonObject params = d["params"];
  if (strcmp(event_type, "mouse_move") == 0) {
    // Take action on a mouse_move event signal
    Serial.println("Got a mouse move event");
    mouse_move(d["params"]);
  } else if (strcmp(event_type, "mouse_click") == 0) {
    // Take action on a mouse_click event signal
    Serial.println("Got a mouse click event");
    mouse_click(d["params"]);
  } else if (strcmp(event_type, "type_string") == 0) {
    // Take action on a (keyboard) type_string event signal
    Serial.println("Got a keyboard type string event");
    type_string(d["params"]);
  }
}


void type_string(JsonObject params) {
  const char* input_string = params["input_string"];
  Serial.print("Sending key: ");
  Serial.print(input_string);
  if (strcmp(input_string, "enter") == 0) {
    Keyboard.write(176);
  } else {
    Keyboard.print(input_string);
  }
}


void mouse_move(JsonObject params) {
  int next_x = params["next_x"]; // cursor's next x position
  int next_y = params["next_y"]; // cursor's next y position
  int current_x = params["current_x"]; // cursor's current x position
  int current_y = params["current_y"]; // cursor's current y position
  // (-128 <-> 127) max values mouse can move in either direction in one call
  // positive x value moves mouse to the right, negative x value moves mouse to the left.
  // positive y value moves the mouse down, negative y value moves the mouse up.
 
  // Print our values
  // Serial.println(next_x);
  // Serial.println(next_y);
  // Serial.println(current_x);
  // Serial.println(current_y);

  // Calculate the distance to move in the x and y directions
  int deltaX = next_x - current_x;
  int deltaY = next_y - current_y;

  // Break the movement into smaller steps, if necessary, to stay within the limits of Mouse.move()
  while (deltaX != 0 || deltaY != 0) {
    int stepX = deltaX;
    int stepY = deltaY;

    // Won't work correctl if giving the max values. probably some c++ memory shenanigans
    if (abs(stepX) > 126) {
      stepX = (stepX > 0) ? 126 : -127;
    }
    if (abs(stepY) > 126) {
      stepY = (stepY > 0) ? 126 : -127;
    }

    Mouse.move(stepX, stepY);
    // Serial.println("Moved mouse");

    deltaX -= stepX;
    deltaY -= stepY;
  }
}


void mouse_click(JsonObject params) {
  const char* params_right_click = params["right_click"]; // true or false
  if (strcmp(params_right_click, "true") == 0) {
    Mouse.click(MOUSE_RIGHT);
  } else {
    Mouse.click();
  }
}
