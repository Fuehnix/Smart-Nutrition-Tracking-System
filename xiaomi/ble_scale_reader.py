import asyncio
from bleak import BleakScanner, BleakClient

# Xiaomi scale service and characteristic UUIDs
SERVICE_UUID = "0000181b-0000-1000-8000-00805f9b34fb"
WEIGHT_CHARACTERISTIC_UUID = "00002a9c-0000-1000-8000-00805f9b34fb"

async def find_xiaomi_scale():
    print("Scanning for Xiaomi scale...")
    devices = await BleakScanner.discover()
    for device in devices:
        if "Xiaomi" in (device.name or ""):
            print(f"Xiaomi scale found: {device.name} - {device.address}")
            return device.address
    return None

async def read_weight(address):
    async with BleakClient(address) as client:
        if client.is_connected:
            print("Connected to the scale. Reading data...")

            data = await client.read_gatt_char(WEIGHT_CHARACTERISTIC_UUID)
            if data:
                weight = int.from_bytes(data[1:3], byteorder="little") / 200
                print(f"Weight: {weight:.2f} kg")
            else:
                print("Failed to read weight data.")
        else:
            print("Failed to connect to the scale.")

async def main():
    scale_address = await find_xiaomi_scale()
    if scale_address:
        await read_weight(scale_address)
    else:
        print("Xiaomi scale not found.")

asyncio.run(main())