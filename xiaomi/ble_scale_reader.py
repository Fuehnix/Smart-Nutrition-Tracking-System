import asyncio
from bleak import BleakClient

# Xiaomi scale MAC address
SCALE_MAC_ADDRESS = "5C:CA:D3:6F:25:2D"

# Xiaomi scale service and characteristic UUIDs
SERVICE_UUID = "0000181b-0000-1000-8000-00805f9b34fb"
WEIGHT_CHARACTERISTIC_UUID = "00002a9c-0000-1000-8000-00805f9b34fb"

async def read_weight():
    async with BleakClient(SCALE_MAC_ADDRESS) as client:
        print("Connected to the scale. Reading data...")

        try:
            data = await client.read_gatt_char(WEIGHT_CHARACTERISTIC_UUID)
            if data:
                raw_weight = int.from_bytes(data[1:3], byteorder="little")
                unit = (data[0] & 0b01)  # Extract unit bit (0: kg, 1: lbs)
                
                if unit == 0:
                    weight = raw_weight / 100  # Xiaomi scales often use a 100 factor
                    print(f"Weight: {weight:.2f} kg")
                else:
                    weight = raw_weight / 100 * 2.20462  # Convert to lbs if needed
                    print(f"Weight: {weight:.2f} lbs")
            else:
                print("Failed to read weight data.")
        except Exception as e:
            print(f"Error reading data: {e}")

asyncio.run(read_weight())