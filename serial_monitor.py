import serial
import sys
import time

PORT = 'COM4'
BAUD = 115200

def monitor():
    print(f"Connecting to ESP32 on {PORT} at {BAUD} baud...")
    print("Press Ctrl+C to exit.\n" + "-"*50)
    try:
        ser = serial.Serial(PORT, BAUD, timeout=0.1)
        while True:
            line = ser.readline()
            if line:
                try:
                    text = line.decode('utf-8', errors='replace')
                    sys.stdout.write(text)
                    sys.stdout.flush()
                except Exception:
                    pass
    except KeyboardInterrupt:
        print("\nDisconnected from serial monitor.")
    except Exception as e:
        print(f"Serial error: {e}")

if __name__ == '__main__':
    monitor()
