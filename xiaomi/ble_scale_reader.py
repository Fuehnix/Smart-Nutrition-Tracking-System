import asyncio
import binascii
from bleak import BleakClient

SCALE_MAC_ADDRESS = "5C:CA:D3:6F:25:2D"
SERVICE_UUID = "0000181b-0000-1000-8000-00805f9b34fb"
WEIGHT_CHARACTERISTIC_UUID = "00002a9c-0000-1000-8000-00805f9b34fb"

def parse_mi_scale_data(sender, data):
    try:
        data = binascii.b2a_hex(data).decode('ascii')
        hex_data = "1b18" + data      # 32 bit alignment
        data2 = bytes.fromhex(data[4:])
        print(f"[Notification] {sender} -> data: {data}, hex_data: {hex_data}, data2: {data2}")

        ctrlByte1 = data2[1]
        isStabilized = ctrlByte1 & (1 << 5)
        hasImpedance = ctrlByte1 & (1 << 1)

        year = int.from_bytes(data2[2:4], byteorder="little")
        month = data2[4]
        day = data2[5]
        date_str = f"{year}-{month:02d}-{day:02d}"

        measunit = data[4:6]
        if len(data) >= 30:
            weight = int((data[28:30] + data[26:28]), 16) * 0.01
            print(f"Extracted weight hex: {data[28:30]} {data[26:28]}")
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
            miimpedance = str(int((data[24:26] + data[22:24]), 16))

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