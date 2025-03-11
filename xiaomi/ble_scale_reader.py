import asyncio
from bleak import BleakClient

ADDRESS = "5C:CA:D3:6F:25:2D"  # body scale BLE address
WEIGHT_CHAR_UUID = "00002a9b-0000-1000-8000-00805f9b34fb"  # weight data UUID

async def read_weight():
    async with BleakClient(ADDRESS) as client:
        if not await client.is_connected():
            print("Fail to connect to body scale!")
            return
        
        print("Success to connect to body scale!")
        weight_data = await client.read_gatt_char(WEIGHT_CHAR_UUID)
        
        # Interprete the weight data
        weight = int.from_bytes(weight_data[:2], byteorder="little") / 200.0  # little endian
        print(f"Weight: {weight} kg")

asyncio.run(read_weight())
