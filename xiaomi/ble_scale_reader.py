import asyncio
from bleak import BleakClient

SCALE_MAC_ADDRESS = "5C:CA:D3:6F:25:2D"  # Replace with the actual MAC address

SERVICE_UUID = "0000181b-0000-1000-8000-00805f9b34fb"
WEIGHT_CHARACTERISTIC_UUID = "00002a9c-0000-1000-8000-00805f9b34fb"

async def read_weight():
    async with BleakClient(SCALE_MAC_ADDRESS) as client:
        print("Connected to scale. Discovering services...")

        try:
            print(f"Reading data from {WEIGHT_CHARACTERISTIC_UUID}...")
            data = await client.read_gatt_char(WEIGHT_CHARACTERISTIC_UUID)
            print(f"Raw Data: {data.hex()}")

            if data:
                # Correct byte parsing
                raw_weight = int.from_bytes(data[1:3], byteorder="little") / 100
                unit_flag = data[0] & 0b01  # 0: kg, 1: lbs

                if unit_flag == 0:
                    print(f"Weight: {raw_weight:.2f} kg")
                else:
                    print(f"Weight: {raw_weight * 2.20462:.2f} lbs")
            else:
                print("Failed to read weight data.")
        except Exception as e:
            print(f"Error: {e}")

asyncio.run(read_weight())