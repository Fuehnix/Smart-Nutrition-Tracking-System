import asyncio
import binascii
from bleak import BleakClient

SCALE_MAC_ADDRESS = "FF:22:07:21:50:4E"  # Replace with the actual address of your scale
CHAR_WRITE = "000036f5-0000-1000-8000-00805f9b34fb"
CHAR_READ = "0000FFF4-0000-1000-8000-00805F9B34FB"
LED_ON_COMMAND = bytearray.fromhex('030A0101000009')
LEF_OFF_COMMAND = bytearray.fromhex('030A0000000009')

SERVICE_UUID = "0000fff0-0000-1000-8000-00805f9b34fb"  # Use the correct service UUID
WEIGHT_CHARACTERISTIC_UUID = "0000fff4-0000-1000-8000-00805f9b34fb"  # The characteristic UUID for weight data

def parse_scale_data(sender, data):
    try:
#        print(f"[Notification] {sender} -> data: {data}, len: {len(data)}")

        if data[0] != 0x03 or len(data) != 10:
            # Basic sanity check
            print(f"Invalid notification: not a Decent Scale? data[0] = {data[0]} len={len(data)}")
            return
        
        weight = ''
        type_ = data[1]
        unit = 'g'
        battery_level = ''

        if type_ == 0xCE:
            # Weight information
            weight = int.from_bytes(data[2:4], byteorder='big', signed=True)/10
            print(f"Weight: {weight:.2f} {unit}")
        elif type_ == 0x0A:            
            # LED on/off -> returns units and battery level
            if data[3] == 0:
                unit = 'g'
            else:
                unit = 'oz'
            battery_level = data[4]
            print(f"battery_lvel: {battery_level}")
        elif type_ == 0xAA:
            # Button press
            print(f"Button press: {data[2]}, duration: {data[3]}")


    except Exception as e:
        print(f"Error parsing data: {e}")

async def read_weight_with_bleak():
    async with BleakClient(SCALE_MAC_ADDRESS) as client:
        try:
            print("Connecting to scale...")

            if client.is_connected:
                print("Already connected.  Disconnecting first...")
                await client.disconnect()
                await asyncio.sleep(1)

            await client.connect()

            # Connect to the scale using BleakClient
            if not client.is_connected:
                print("Failed to connect!")
                return

            print("Connected to scale. Fetching services...")

            # Write Led on, need to write something to read 
            await client.write_gatt_char(CHAR_WRITE, LED_ON_COMMAND)
            await asyncio.sleep(1)

            # Get services and ensure the desired service is available
            services = await client.get_services()

            if SERVICE_UUID not in [s.uuid for s in services]:
                print(f"Service {SERVICE_UUID} not found!")
                return

            print("Service found. Enabling notifications...")

            # Start notifications for the weight characteristic
            await client.start_notify(WEIGHT_CHARACTERISTIC_UUID, parse_scale_data)
            await asyncio.sleep(10)  # Keep reading for 10 seconds
            await client.stop_notify(WEIGHT_CHARACTERISTIC_UUID)

        except Exception as e:
            print(f"Error: {e}")
        finally:
            if client.is_connected:
                await client.disconnect()
            print("Disconnected from scale")

# Run the asyncio event loop to start reading from the scale
asyncio.run(read_weight_with_bleak())