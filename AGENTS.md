# 🤖 AGENT INSTRUCTIONS FOR THIS WORKSPACE

When working on this repository or any ESP32 project using this hardware, **YOU MUST READ AND ADHERE TO**:
👉 **[HARDWARE_BLUEPRINT.md](file:///c:/Users/gcayd/OneDrive/Desktop/code/esp32/HARDWARE_BLUEPRINT.md)**

### Key Invariants:
1. **Never allocate large HTML/JS strings in Python files:** Stream `index.html` in 1KB chunks to avoid `MemoryError`.
2. **OLED Hardware:** SSD1306 128x64 on I2C(0) `SDA=21`, `SCL=22`, address `0x3C`. Note the physical split: Top 16px is Yellow, bottom 48px is Blue.
3. **Serial & Flashing:** `COM4` at `115200` baud using `python sync_esp.py`.
4. **Time & Secrets:** NTP sync on boot with UTC+3 offset. Always keep `config.json` in `.gitignore`.
