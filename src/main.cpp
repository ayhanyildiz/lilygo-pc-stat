#include <Arduino.h>
#include <TFT_eSPI.h>
#include <math.h>
#include <esp_system.h>

TFT_eSPI screen;
TFT_eSprite canvas(&screen);
constexpr uint16_t BG = 0x0841, TRACK = 0x2124, MUTED = 0x8c71;
const uint16_t colors[] = {0x57ef, 0x2e7f, 0xb45f};
const char *labels[] = {"GPU", "CPU", "MEM"};
const uint8_t metricOrder[] = {1, 0, 2};
float values[] = {-1, -1, -1, -1};
uint32_t lastFrame = 0;
bool received = false, stale = true;
char line[128];
size_t used = 0;
bool overflow = false;
uint8_t rotation = 2;

void draw() {
  canvas.fillSprite(BG);
  for (int i = 0; i < 3; ++i) {
    int y = 26 + i * 54;
    float value = values[metricOrder[i]];
    bool valid = !stale && value >= 0;
    canvas.drawSmoothArc(40, y, 24, 21, 0, 360, TRACK, BG);
    if (valid && value > 0) {
      uint32_t angle = max(1, int(roundf(value * 3.6f)));
      // TFT_eSPI measures from 6 o'clock; 180 degrees is 12 o'clock.
      if (angle >= 360)
        canvas.drawSmoothArc(40, y, 24, 21, 0, 360, colors[i], BG);
      else
        canvas.drawSmoothArc(40, y, 24, 21, 180, (180 + angle) % 360,
                             colors[i], BG, true);
    }
    canvas.setTextDatum(TC_DATUM);
    canvas.setTextColor(valid ? TFT_WHITE : MUTED, BG);
    char text[12];
    if (valid) snprintf(text, sizeof(text), "%.0f%%", value);
    else snprintf(text, sizeof(text), "--");
    canvas.drawString(text, 40, y - 13, 2);
    canvas.setTextColor(colors[i], BG);
    canvas.drawString(labels[i], 40, y + 6, 1);
  }
  canvas.pushSprite(0, 0);
}

void processLine() {
  if (!strcmp(line, "HELLO")) {
    Serial.println("PCMON,1");
    return;
  }
  unsigned long seq;
  float next[4];
  int consumed = 0;
  if (sscanf(line, "M,%lu,%f,%f,%f,%f%n", &seq, &next[0], &next[1],
             &next[2], &next[3], &consumed) != 5 || line[consumed]) return;
  for (float value : next)
    if (!isfinite(value) || (value != -1 && (value < 0 || value > 100))) return;
  memcpy(values, next, sizeof(values));
  lastFrame = millis();
  received = true;
  stale = false;
  draw();
  Serial.printf("ACK,%lu\n", seq);
}

void setup() {
  pinMode(38, OUTPUT);
  digitalWrite(38, HIGH);
  pinMode(0, INPUT_PULLUP);
  Serial.begin(115200);
  Serial.printf("PCMON boot reset=%d\n", int(esp_reset_reason()));
  Serial.println("PCMON display init");
  screen.init();
  Serial.println("PCMON display initialized");
  screen.setRotation(rotation);
  canvas.setColorDepth(16);
  if (!canvas.createSprite(80, 160)) {
    screen.fillScreen(TFT_BLACK);
    screen.setTextColor(TFT_RED);
    screen.drawString("Display memory error", 0, 20, 1);
    return;
  }
  draw();
  digitalWrite(38, LOW); // T-Dongle-S3 backlight is active low.
  Serial.println("PCMON ready");
}

void loop() {
  // Bound serial work so a noisy sender cannot starve display/button handling.
  for (int n = 0; n < 256 && Serial.available(); ++n) {
    char c = Serial.read();
    if (c == '\n') {
      line[used] = 0;
      if (!overflow) processLine();
      used = 0;
      overflow = false;
    } else if (c != '\r') {
      if (used < sizeof(line) - 1) line[used++] = c;
      else overflow = true;
    }
  }
  if (!stale && received && millis() - lastFrame > 4500) {
    stale = true;
    draw();
  }
  static bool previous = HIGH, stable = HIGH;
  static uint32_t changed = 0;
  bool button = digitalRead(0);
  if (button != previous) { previous = button; changed = millis(); }
  if (button != stable && millis() - changed > 40) {
    stable = button;
    if (!stable) { rotation = rotation == 0 ? 2 : 0; screen.setRotation(rotation); draw(); }
  }
  delay(2);
}
