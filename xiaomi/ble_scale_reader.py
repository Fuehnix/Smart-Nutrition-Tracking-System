import asyncio
import binascii
from bleak import BleakClient

SCALE_MAC_ADDRESS = "5C:CA:D3:6F:25:2D"
SERVICE_UUID = "0000181b-0000-1000-8000-00805f9b34fb"
WEIGHT_CHARACTERISTIC_UUID = "00002a9c-0000-1000-8000-00805f9b34fb"

def parse_mi_scale_data(sender, data):
    try:
        hex_data = data.hex()
        print(f"[Notification] {sender} -> Raw Data: {hex_data}")

        data2 = bytes.fromhex(hex_data)
        ctrlByte1 = data2[1]
        isStabilized = ctrlByte1 & (1 << 5)
        hasImpedance = ctrlByte1 & (1 << 1)

        year = int.from_bytes(data2[2:4], byteorder="little")
        month = data2[4]
        day = data2[5]
        date_str = f"{year}-{month:02d}-{day:02d}"


        weight_raw = int.from_bytes(data2[6:8], byteorder="little")
        measured = weight_raw * 0.1 

        unit_code = data2[0] & 0xF0
        if unit_code == 0x00:
            unit = 'kg'
        elif unit_code == 0x10:
            unit = 'lbs'
            measured *= 0.453592 
        else:
            unit = 'unknown'

        miimpedance = "N/A"
        if hasImpedance and len(data2) >= 10:
            miimpedance = int.from_bytes(data2[8:10], byteorder="little") 

        print(f"Weight: {measured:.2f} {unit}, Stabilized: {bool(isStabilized)}, Impedance: {miimpedance}")
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