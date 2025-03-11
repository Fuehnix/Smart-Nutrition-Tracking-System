import asyncio
from bleak import BleakClient

# Xiaomi scale MAC address
SCALE_MAC_ADDRESS = "5C:CA:D3:6F:25:2D"

# Xiaomi scale service and characteristic UUIDs
SERVICE_UUID = "0000181b-0000-1000-8000-00805f9b34fb"
WEIGHT_CHARACTERISTIC_UUID = "00002a9c-0000-1000-8000-00805f9b34fb"

async def read_weight():
    async with BleakClient(SCALE_MAC_ADDRESS) as client:
        print("Connected to the scale. Discovering services...")

        try:
            services = client.services
            for service in services:
                print(f"Service: {service.uuid}")
                for char in service.characteristics:
                    print(f"  Characteristic: {char.uuid}")

            print(f"Reading data from {WEIGHT_CHARACTERISTIC_UUID}...")
            data = await client.read_gatt_char(WEIGHT_CHARACTERISTIC_UUID)
            print(f"Raw data: {data.hex()}")

            if data:
                raw_weight = int.from_bytes(data[1:3], byteorder="little")
                unit = data[0] & 0b01  

                if unit == 0:
                    weight = raw_weight / 100  
                    print(f"Weight: {weight:.2f} kg")
                else:
                    weight = raw_weight / 100 * 2.20462  
                    print(f"Weight: {weight:.2f} lbs")
            else:
                print("Failed to read weight data.")
        except Exception as e:
            print(f"Error reading data: {e}")

asyncio.run(read_weight())