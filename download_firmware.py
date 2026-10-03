import urllib.request
import re
import os

url = "https://micropython.org/download/ESP32_GENERIC/"
print("Fetching MicroPython firmware list...")
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
html = urllib.request.urlopen(req).read().decode('utf-8')

# Find stable .bin links
matches = re.findall(r'href="(/resources/firmware/ESP32_GENERIC-[^"]+\.bin)"', html)
stable_matches = [m for m in matches if "preview" not in m]

if not stable_matches:
    stable_matches = matches

if stable_matches:
    firmware_rel_url = stable_matches[0]
    full_url = "https://micropython.org" + firmware_rel_url
    filename = os.path.basename(firmware_rel_url)
    print(f"Downloading latest stable firmware: {filename} from {full_url}")
    urllib.request.urlretrieve(full_url, filename)
    print(f"Download complete: {filename} ({os.path.getsize(filename)} bytes)")
else:
    print("No firmware found!")
