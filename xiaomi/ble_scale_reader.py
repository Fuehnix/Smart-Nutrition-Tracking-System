import asyncio
from bleak import BleakClient

SCALE_MAC_ADDRESS = "5C:CA:D3:6F:25:2D"

async def read_weight():
    async with BleakClient(SCALE_MAC_ADDRESS) as client:
        print("Connected to scale. Discovering services...")

        try:
            if not client.is_connected:
                await client.connect()
            
            print("Connected to scale. Discovering services...")

            services = await client.get_services()

            if not services:
                print("No services found")
                await asyncio.sleep(1)
                services = await client.get_services()

            if not services:
                print("No services found after retrying")
                return

            for service in services:
                print(f"\n[Service] {service.uuid}")

                for char in service.characteristics:
                    try:
                        if "read" in char.properties:
                            data = await client.read_gatt_char(char.uuid)
                            hex_data = data.hex()
                            print(f"  [Characteristic] {char.uuid} -> Raw Data: {hex_data}")
                        else:
                            print(f"  [Characteristic] {char.uuid} (No read property)")

                    except Exception as e:
                        print(f"  [Characteristic] {char.uuid} -> Read Error: {e}")

        except Exception as e:
            print(f"Error: {e}")

        finally:
            await client.disconnect()
            print("Disconnected from scale")

asyncio.run(read_weight())