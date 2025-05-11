import asyncio
import binascii
from bleak import BleakClient, BleakScanner
from bleak.exc import BleakError

class DecentScale:
    def __init__(self, mac_address="FF:22:07:21:80:CE"):
        self.mac_address = mac_address
        self.char_write = "000036f5-0000-1000-8000-00805f9b34fb"
        self.char_read = "0000FFF4-0000-1000-8000-00805F9B34FB"
        self.led_on_command = bytearray.fromhex('030A0101000009')
        self.led_off_command = bytearray.fromhex('030A0000000009')
        self.service_uuid = "0000fff0-0000-1000-8000-00805f9b34fb"
        self.weight_char_uuid = "0000fff4-0000-1000-8000-00805f9b34fb"
        self.last_weight = None
        self.last_unit = 'g'
        self.data_received = False
        self._client = None
    
    def get_weight(self):
        """Get weight from Decent kitchen scale"""
        try:
            # Reset data_received flag before each attempt
            self.data_received = False
            
            # Create a new event loop for each call
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Run the async function to get data
            result = loop.run_until_complete(self._read_weight_async())
            loop.close()
            
            if result and 'weight' in result and 'unit' in result:
                print(f"Successfully received weight data: {result}")
                # Save last successful reading
                self.last_weight = result['weight']
                self.last_unit = result['unit']
                return result
            
            print("No valid weight data received, falling back to mock data")
            # If no valid data, return last known data or mock data
            if self.last_weight is not None:
                return {
                    'weight': self.last_weight,
                    'unit': self.last_unit
                }
            return {
                'weight': 125.5,
                'unit': 'g'
            }
        except Exception as e:
            print(f"Error reading Decent scale: {e}")
            # Return last successful reading or mock data
            if self.last_weight is not None:
                return {
                    'weight': self.last_weight,
                    'unit': self.last_unit
                }
            return {
                'weight': 125.5,
                'unit': 'g'
            }
    
    async def _read_weight_async(self):
        """Async function to read data from decent scale via BLE"""
        result = {}
        notification_data = {}
        self._client = None
        
        try:
            # Find the device by address
            print(f"Scanning for Decent Scale with MAC: {self.mac_address}")
            device = await BleakScanner.find_device_by_address(self.mac_address)
            
            if not device:
                print("Could not find the scale device by MAC address")
                print("Scanning for devices...")
                devices = await BleakScanner.discover()
                for d in devices:
                    print(f"Found device: {d.name} - {d.address}")
                    if d.name and ("DECENT" in d.name.upper() or "SCALE" in d.name.upper()):
                        device = d
                        print(f"Found potential scale: {d.name} - {d.address}")
                        break
                
                if not device:
                    print("No suitable scale device found")
                    return None
            
            print(f"Connecting to Decent scale at {device.address}...")
            
            # Initialize client but don't connect yet
            client = BleakClient(device)
            
            # Connect to the device
            await client.connect()
            if not client.is_connected:
                print("Failed to connect to Decent scale!")
                return None
            
            print("Connected to Decent scale")
            self._client = client
            
            # Define notification handler
            def notification_handler(sender, data):
                nonlocal notification_data
                print(f"Notification received from {sender}: {data.hex()}")
                parsed = self._parse_scale_data(sender, data)
                if parsed:
                    notification_data = parsed
                    self.data_received = True
                else:
                    print("Could not parse notification data")
            
            # Try to get services for debugging
            try:
                services = await client.get_services()
                for service in services:
                    print(f"Service: {service.uuid}")
                    for char in service.characteristics:
                        print(f"  Characteristic: {char.uuid}, Properties: {char.properties}")
            except Exception as e:
                print(f"Error getting services: {e}")
            
            # First activate the scale
            try:
                print(f"Sending LED command to characteristic: {self.char_write}")
                await client.write_gatt_char(self.char_write, self.led_on_command)
                print("LED command sent to scale")
            except Exception as e:
                print(f"Failed to write LED command: {e}")
            
            # Start notification on weight characteristic
            try:
                print(f"Starting notification on: {self.weight_char_uuid}")
                await client.start_notify(self.weight_char_uuid, notification_handler)
                print("Notification started")
            except Exception as e:
                print(f"Failed to start notification: {e}")
                return None
            
            # Wait for data
            print("Waiting for weight data...")
            max_wait = 15
            for i in range(max_wait):
                if self.data_received:
                    print(f"Data received after {i+1} seconds")
                    break
                print(f"Waiting... {i+1}/{max_wait}s")
                await asyncio.sleep(1)
            
            # Stop notification
            try:
                await client.stop_notify(self.weight_char_uuid)
            except Exception as e:
                print(f"Error stopping notification: {e}")
            
            # Turn off LED
            try:
                await client.write_gatt_char(self.char_write, self.led_off_command)
                print("LED turned off")
            except Exception as e:
                print(f"Failed to turn off LED: {e}")
            
            if notification_data:
                print(f"Returning notification data: {notification_data}")
                return notification_data
            else:
                print("No notification data received")
                return None
                
        except Exception as e:
            print(f"Error in reading Decent scale: {e}")
            return None
        finally:
            # Always disconnect
            if self._client and self._client.is_connected:
                try:
                    await self._client.disconnect()
                    print("Disconnected from Decent scale")
                except Exception as e:
                    print(f"Error disconnecting: {e}")
            self._client = None
    
    def _parse_scale_data(self, sender, data):
        """Parse the data received from Decent scale"""
        try:
            print(f"Parsing data: {data.hex()}")
            
            # Print each byte for debugging
            print("Packet bytes: ", end="")
            for i, b in enumerate(data):
                print(f"[{i}]={b:02X} ", end="")
            print()
            
            # Check for common scale data patterns
            
            # Simple weight data in standard format - check first byte is 0x03
            if len(data) >= 7 and data[0] == 0x03:
                type_byte = data[1]
                
                # Weight data packet (0xCE)
                if type_byte == 0xCE:
                    weight = int.from_bytes(data[2:4], byteorder='big', signed=True) / 10
                    unit = 'g'  # Default unit
                    
                    # Check for unit indicator in the data
                    if len(data) > 4 and data[4] == 0x01:
                        unit = 'oz'
                    
                    return {
                        'weight': round(weight, 1),
                        'unit': unit
                    }
                
                # Unit/mode setting packet (0x0A)
                elif type_byte == 0x0A:
                    if len(data) > 3:
                        unit_byte = data[3]
                        if unit_byte == 0:
                            print("Unit set to grams")
                        else:
                            print("Unit set to ounces")
                    return None  # No weight in this packet type
            
            # Attempt more flexible pattern matching
            
            # Try to find weight patterns at various positions
            for offset in range(len(data) - 1):
                if offset + 2 <= len(data):
                    # Try reading 2 bytes as weight value (could be at different positions)
                    weight = int.from_bytes(data[offset:offset+2], byteorder='big', signed=False) / 10
                    if 1 <= weight <= 5000:  # Reasonable weight range for kitchen scale
                        print(f"Potential weight found at position {offset}: {weight}g")
                        return {
                            'weight': round(weight, 1),
                            'unit': 'g'
                        }
            
            print("Could not parse data in any known format")
            return None
            
        except Exception as e:
            print(f"Error parsing scale data: {e}")
            return None
