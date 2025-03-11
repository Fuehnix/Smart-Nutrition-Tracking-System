import asyncio
from bleak import BleakClient

SCALE_MAC_ADDRESS = "5C:CA:D3:6F:25:2D"  # Replace with actual MAC address
SERVICE_UUID = "0000181b-0000-1000-8000-00805f9b34fb"

async def read_weight():
    async with BleakClient(SCALE_MAC_ADDRESS) as client:
        print("Connected to scale. Discovering services...")

        try:
            services = await client.get_services()
            for service in services:
                if service.uuid == SERVICE_UUID:
                    for char in service.characteristics:
                        if "read" in char.properties:
                            print(f"Reading data from {char.uuid}...")
                            data = await client.read_gatt_char(char.uuid)
                            print(f"Raw Data: {data.hex()}")

                            if len(data) >= 30:
                                # Extract weight
                                measured = int(data[28:30].hex() + data[26:28].hex(), 16) * 0.01

                                # Extract measurement unit
                                measunit = data[4:6].hex()  # Convert to hex string

                                if measunit == "03":
                                    unit = "lbs"
                                elif measunit == "02":
                                    unit = "kg"
                                    measured /= 2  # Convert to correct kg value

                                print(f"Weight: {measured:.2f} {unit}")
                            else:
                                print("Invalid data received from scale.")
        except Exception as e:
            print(f"Error: {e}")

asyncio.run(read_weight())