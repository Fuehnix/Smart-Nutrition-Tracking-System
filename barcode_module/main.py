import time
import json
from barcode_scanner import BarcodeScanner
from nutrition_api import NutritionAPI


def main():
    print("Starting Smart Nutrition Tracking System - Barcode Module")
    
    # Initialize barcode scanner
    scanner = BarcodeScanner()
    if not scanner.connect():
        print("Failed to connect to barcode scanner. Please check connections.")
        # Uncomment these lines if you want to use camera as a fallback
        # print("Trying camera scanner instead...")
        # scanner = CameraScanner()
        # if not scanner.connect():
        # print("Failed to initialize camera scanner. Exiting.")
        # return
    
    # Initialize nutrition API client
    nutrition_api = NutritionAPI()
    
    print("\nWelcome to the Smart Nutrition Tracking System!")
    print("----------------------------------------------")
    print("For packaged products WITH barcodes: Scan the barcode")
    print("For items WITHOUT barcodes: Simply type the product name")
    print("----------------------------------------------")
    
    try:
        while True:
            # Read barcode from scanner
            barcode_input = input("Scan barcode or type product name: ")
            barcode = barcode_input.strip()            
            if barcode:
                # Check if input looks like a barcode or a product name
                is_likely_barcode = barcode.isdigit() or (sum(c.isdigit() for c in barcode) > len(barcode) * 0.7)
                
                if is_likely_barcode:
                    print(f"\nProcessing barcode: {barcode}")
                    # Get nutrition data for the barcode
                    nutrition_data = nutrition_api.get_nutrition_data(barcode)
                else:
                    print(f"\nProcessing product name: {barcode}")
                    # Skip database lookups and go straight to ChatGPT for product names
                    nutrition_data = nutrition_api.get_nutrition_from_chatgpt(barcode)
                
                if nutrition_data:
                    print("\n Nutrition data found!")
                    print(f"Source: {nutrition_data.get('source', 'Unknown')}")
                    print(f"Product: {nutrition_data.get('name', 'Unknown Product')}")
                    print(f"Serving Size: {nutrition_data.get('serving_size', 'Unknown')}")
                    print("\nNutrition Facts (per serving):")
                    print(f"Calories: {nutrition_data.get('calories', 0)}")
                    print(f"Protein: {nutrition_data.get('protein_g', 0)}g")
                    print(f"Carbohydrates: {nutrition_data.get('carbs_g', 0)}g")
                    print(f"Fat: {nutrition_data.get('fat_g', 0)}g")
                    print(f"Sugar: {nutrition_data.get('sugar_g', 0)}g")
                    print(f"Fiber: {nutrition_data.get('fiber_g', 0)}g")
                    print(f"Sodium: {nutrition_data.get('sodium_mg', 0)}mg")
                else:
                    print("\n No nutrition data found for this barcode.")
                    product_name = input("Enter product name for estimation (or press Enter to skip): ")
                    if product_name:
                        nutrition_data = nutrition_api.get_nutrition_from_chatgpt(product_name)
                        if nutrition_data:
                            print("\n Estimated nutrition data (from ChatGPT):")
                            print(f"Product: {nutrition_data.get('name', product_name)}")
                            print(f"Serving Size: {nutrition_data.get('serving_size', 'Unknown')}")
                            print("\nNutrition Facts (per serving):")
                            print(f"Calories: {nutrition_data.get('calories', 0)}")
                            print(f"Protein: {nutrition_data.get('protein_g', 0)}g")
                            print(f"Carbohydrates: {nutrition_data.get('carbs_g', 0)}g")
                            print(f"Fat: {nutrition_data.get('fat_g', 0)}g")
                            print(f"Sugar: {nutrition_data.get('sugar_g', 0)}g")
                            print(f"Fiber: {nutrition_data.get('fiber_g', 0)}g")
                            print(f"Sodium: {nutrition_data.get('sodium_mg', 0)}mg")
                        else:
                            print("Could not estimate nutrition data.")
                
                print("\nReady for next scan...\n")
            
            # Small delay to prevent CPU hogging
            time.sleep(0.1)
    
    except KeyboardInterrupt:
        print("\nProgram terminated by user")
    finally:
        scanner.close()

if __name__ == "__main__":
    main()
