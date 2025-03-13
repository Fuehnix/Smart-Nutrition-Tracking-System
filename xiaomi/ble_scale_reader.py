import asyncio
from bleak import BleakClient

SCALE_MAC_ADDRESS = "5C:CA:D3:6F:25:2D"  # 
TARGET_SERVICE_UUID = "0000181b-0000-1000-8000-00805f9b34fb"
WEIGHT_CHARACTERISTIC_UUID = "00002a9c-0000-1000-8000-00805f9b34fb"

async def read_weight():
    async with BleakClient(SCALE_MAC_ADDRESS) as client:
        print("Connected to scale. Discovering services...")

        try:
            await client.connect()
            if not client.is_connected:
                print("Failed to connect to scale")
                return
            
            print("Connected to scale. Discovering services...")

            services = await client.get_services()

            if not services:
                print("No services found")
                await asyncio.sleep(1)
                services = await client.get_services()

            if not services:
                print("No services found after retrying")
                return


            for service in services:
                if service.uuid.lower() == TARGET_SERVICE_UUID:
                    print(f"\n[Service] {service.uuid}")

                    for char in service.characteristics:
                        if "read" in char.properties:
                            try:
                                data = await client.read_gatt_char(char.uuid)
                                hex_data = data.hex()
                            
                                # If it's the weight characteristic, process separately
                                if char.uuid.lower() == WEIGHT_CHARACTERISTIC_UUID:
                                    print(f"  [WEIGHT] {char.uuid} -> Raw Data: {hex_data}")

                                    if len(data) >= 10:
                                        measured = int.from_bytes(data[6:8], byteorder="little") * 0.01
                                        measunit = data[4]

                                        if measunit == 0x03:
                                            unit = "lbs"
                                        elif measunit == 0x02:
                                            unit = "kg"
                                            measured /= 2  
                                        else:
                                            print("  Unknown measurement unit.")
                                            continue

                                        print(f"  Weight: {measured:.2f} {unit}")
                                    else:
                                        print("  Invalid weight data received.")
                                else:
                                    # Print other characteristics normally
                                    print(f"  [Characteristic] {char.uuid} -> Raw Data: {hex_data}")

                            except Exception as e:
                                print(f"  [Characteristic] {char.uuid} -> Read Error: {e}")

        except Exception as e:
            print(f"Error: {e}")

        finally:
            await client.disconnect()
            print("Disconnected from scale")

asyncio.run(read_weight())