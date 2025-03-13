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

        measunit = hex_data[0:2]
        measured = int((hex_data[10:12] + hex_data[12:14]), 16) * 0.01

        unit = ''
        if measunit == "03":
            unit = 'lbs'
        elif measunit == "02":
            unit = 'kg'
            measured = measured 

        miimpedance = int((hex_data[8:10] + hex_data[6:8]), 16)

        print(f"Weight: {measured} {unit}, Stabilized: {bool(isStabilized)}, Impedance: {miimpedance if hasImpedance else 'N/A'}")
    except Exception as e:
        print(f"Error parsing data: {e}")

async def read_weight():
    async with BleakClient(SCALE_MAC_ADDRESS) as client:
        try:
            print("Connecting to scale...")

            await client.connect()  # 무조건 연결 시도

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