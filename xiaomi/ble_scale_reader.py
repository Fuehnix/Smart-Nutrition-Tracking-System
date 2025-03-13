import asyncio
from bleak import BleakClient

SCALE_MAC_ADDRESS = "5C:CA:D3:6F:25:2D"  
WEIGHT_CHARACTERISTIC_UUID = "00002a9c-0000-1000-8000-00805f9b34fb"

def weight_measurement_callback(sender, data):
    """ Weight Measurement Data Processing """
    hex_data = data.hex()
    print(f"[Notification] {sender} -> Raw Data: {hex_data}")

    if len(data) >= 10:
        measured = int.from_bytes(data[6:8], byteorder="little") * 0.01
        measunit = data[4]

        if measunit == 0x03:
            unit = "lbs"
        elif measunit == 0x02:
            unit = "kg"
            measured /= 2  # 
        else:
            print("  Unknown measurement unit.")
            return

        print(f"  Weight: {measured:.2f} {unit}")
    else:
        print("  Invalid weight data received.")

async def read_weight():
    async with BleakClient(SCALE_MAC_ADDRESS) as client:
        print("Connected to scale. Discovering services...")

        try:
            if not client.is_connected:
                await client.connect()

            print("Connected. Enabling weight measurement notifications...")

            # Weight Measurement (00002a9c) 
            await client.start_notify(WEIGHT_CHARACTERISTIC_UUID, weight_measurement_callback)

            # wait for 10 seconds
            await asyncio.sleep(10)

            # 
            await client.stop_notify(WEIGHT_CHARACTERISTIC_UUID)

        except Exception as e:
            print(f"Error: {e}")

        finally:
            await client.disconnect()
            print("Disconnected from scale")

asyncio.run(read_weight())