import time

class BarcodeScanner:
    def __init__(self):
        self.keyboard_mode = True
        
    def connect(self):
        """Connect to the barcode scanner"""
        print("Using scanner in keyboard emulation mode")
        print("When prompted, scan a barcode or type it manually")
        return True
    
    def read_barcode(self):
        """Read barcode data from the scanner"""
        barcode = input("Scan a barcode (or type it manually and press Enter): ")
        if barcode:
            print(f"Barcode received: {barcode}")
            return barcode
        return None
    
    def close(self):
        """Close the connection to the scanner"""
        print("Scanner session ended")