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

        # Ensure the service exists
        services = await client.get_services()
        service = services.get_service(SERVICE_UUID)
        if not service:
            print(f"Service {SERVICE_UUID} not found.")
            return

        print(f"Service {SERVICE_UUID} found. Reading data...")

        try:
            data = await client.read_gatt_char(WEIGHT_CHARACTERISTIC_UUID)
            if data:
                weight = int.from_bytes(data[1:3], byteorder="little") / 200
                print(f"Weight: {weight:.2f} kg")
            else:
                print("Failed to read weight data.")
        except Exception as e:
            print(f"Error reading data: {e}")

asyncio.run(read_weight())