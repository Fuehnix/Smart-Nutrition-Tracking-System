import asyncio
from bleak import BleakClient

ADDRESS = "5C:CA:D3:6F:25:2D"  # body scale MAC address

async def discover_services():
    async with BleakClient(ADDRESS) as client:
        services = await client.get_services()
        for service in services:
            print(f"service: {service.uuid}")
            for char in service.characteristics:
                print(f"characteristics: {char.uuid} (handle: 0x{char.handle:X})")

asyncio.run(discover_services())