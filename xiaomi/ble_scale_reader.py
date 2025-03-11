import asyncio
from bleak import BleakScanner

async def scan():
    print("Scanning for BLE devices...")
    devices = await BleakScanner.discover()
    for device in devices:
        print(f"Device: {device.name}, Address: {device.address}")

asyncio.run(scan())

