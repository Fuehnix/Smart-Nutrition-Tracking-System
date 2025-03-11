import asyncio
from bleak import BleakClient

ADDRESS = "5C:CA:D3:6F:25:2D"  # Replace with your scale's Bluetooth address

async def read_all_characteristics():
    async with BleakClient(ADDRESS) as client:
        if not client.is_connected:
            print("Failed to connect to the scale")
            return
        
        print("Connected to the scale")

        for service in client.services:
            print(f"\nService: {service.uuid}")
            for char in service.characteristics:
                try:
                    value = await client.read_gatt_char(char.uuid)
                    print(f"  {char.uuid} (Handle: {char.handle}) → {value.hex()}")
                except:
                    print(f"  {char.uuid} (Handle: {char.handle}) → Read failed")

asyncio.run(read_all_characteristics())