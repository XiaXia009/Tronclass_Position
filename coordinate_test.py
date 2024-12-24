#23.70213663906112, 120.42895980953193

import random


data = "23.70213663906112, 120.42895980953193"
latitude, longitude = data.replace(" ", "").split(",")

print(f"緯度: {latitude}")
print(f"經度: {longitude}")

import random

print(float(f"30.{''.join([str(random.randint(0, 9)) for _ in range(15)])}"))
print(float(f"1{random.randint(0, 9)}.{''.join([str(random.randint(0, 9)) for _ in range(15)])}"))
