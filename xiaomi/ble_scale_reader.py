import asyncio
import binascii
from bleak import BleakClient

SCALE_MAC_ADDRESS = "5C:CA:D3:6F:25:2D"
SERVICE_UUID = "0000181b-0000-1000-8000-00805f9b34fb"
WEIGHT_CHARACTERISTIC_UUID = "00002a9c-0000-1000-8000-00805f9b34fb"

def parse_mi_scale_data(sender, data):
    try:
        data = binascii.b2a_hex(data).decode('ascii')
        print(f"[Notification] {sender} -> data: {data}")

        ctrlByte1 = data[2:3]
        isStabilized = ctrlByte1 & (1 << 5)
        hasImpedance = ctrlByte1 & (1 << 1)

        year = int.from_bytes(data[4:7], byteorder="little")
        month = data[8:9]
        day = data[10:11]
        date_str = f"{year}-{month:02d}-{day:02d}"

        measunit = data[0:1]
        if len(data) >= 20:
            weight = int((data[24:25] + data[22:23]), 16) * 0.01
            print(f"Extracted weight hex: {data[24:25]} {data[22:23]}")
        else:
            weight = 0

        unit = ''
        if measunit == "03": 
            unit = 'lbs'
        elif measunit == "02": 
            unit = 'kg' 
            weight = weight / 2

        miimpedance = "N/A"
        if hasImpedance:
            miimpedance = str(int((data[20:21] + data[18:19]), 16))

        print(f"Date: {date_str}, Weight: {weight:.2f} {unit}, Stabilized: {bool(isStabilized)}, Impedance: {miimpedance}")
    except Exception as e:
        print(f"Error parsing data: {e}")

async def read_weight():
    async with BleakClient(SCALE_MAC_ADDRESS) as client:
        try:
            print("Connecting to scale...")

            if client.is_connected:
                print("Already connected.  Disconnecting first...")
                await client.disconnect()
                await asyncio.sleep(1)


            await client.connect()  # try connecting again

            if not client.is_connected:
                print("Failed to connect!")
                return
            
            print("Connected to scale. Fetching services...")

            services = await client.get_services()
            if SERVICE_UUID not in [s.uuid for s in services]:
                print(f"Service {SERVICE_UUID} not found!")
                return

            print("Service found. Enabling notifications...")

            await client.start_notify(WEIGHT_CHARACTERISTIC_UUID, parse_mi_scale_data)
            await asyncio.sleep(10)
            await client.stop_notify(WEIGHT_CHARACTERISTIC_UUID)

        except Exception as e:
            print(f"Error: {e}")
        finally:
            if client.is_connected:
                await client.disconnect()
            print("Disconnected from scale")

asyncio.run(read_weight())