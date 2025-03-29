#include <ArduinoJson.h>

const int BUFFER_SIZE = 256;  // Adjust buffer size as needed
char jsonBuffer[BUFFER_SIZE];

void setup() {
    Serial.begin(115200);
    while (!Serial) {
        ;  // Wait for serial port to connect (for boards like Leonardo)
    }
    Serial.println("Arduino Ready - Waiting for JSON data...");
}

void loop() {
    if (Serial.available()) {
        delay(100);  // Small delay to ensure full message is received
        int len = Serial.readBytesUntil('\n', jsonBuffer, BUFFER_SIZE - 1);
        jsonBuffer[len] = '\0';  // Null-terminate the string

        Serial.print("Received JSON: ");
        Serial.println(jsonBuffer);

        // Parse JSON
        StaticJsonDocument<BUFFER_SIZE> doc;
        DeserializationError error = deserializeJson(doc, jsonBuffer);

        if (error) {
            Serial.print("JSON Parsing Failed: ");
            Serial.println(error.c_str());
            return;
        }

        // Process the received JSON data
        Serial.println("Processed Region Values:");
        for (JsonPair region : doc.as<JsonObject>()) {
            const char* regionId = region.key().c_str();
            int value = region.value()["value"];  // Extract the value field

            Serial.print("Region ");
            Serial.print(regionId);
            Serial.print(": ");
            Serial.println(value);

            // TODO: Map `value` to motor control logic if needed
        }

        Serial.println("---- JSON Processing Complete ----\n");
    }
}