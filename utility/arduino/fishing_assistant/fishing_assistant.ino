#include <Keyboard.h>
#include <Mouse.h>
#include <ArduinoJson.h>

// "reaction time" between key presses
const unsigned int LOWER_REACTION = 180;
const unsigned int UPPER_REACTION = 310;

// Screen resolution for cursor movements
const unsigned int DISPLAY_WIDTH = 1920;
const unsigned int DISPLAY_HEIGHT = 1080;


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
  const char* params_input_string = params["input_string"];
  Serial.print("Typing string: ");
  Serial.print(params_input_string);
  Keyboard.print(params_input_string);
}


void mouse_move(JsonObject params) {
  const char* params_next_x = params["next_x"]; // cursor's next x position
  const char* params_next_y = params["next_y"]; // cursor's next y position
  const char* params_current_x = params["current_x"]; // cursor's current x position
  const char* params_current_y = params["current_y"]; // cursor's current y position
}


void mouse_click(JsonObject params) {
  const char* params_right_click = params["right_click"]; // true or false
  if (strcmp(params_right_click, "true") == 0) {
    Mouse.click(MOUSE_RIGHT);
  } else {
    Mouse.click();
  }
}
