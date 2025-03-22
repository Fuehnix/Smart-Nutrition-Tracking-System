# Barcode Scanning & Nutrition API Module

## Overview
This module handles barcode scanning functionality and nutrition data retrieval for the Smart Nutrition Tracking System. It provides automated product identification via barcode scanning and retrieves detailed nutrition information from multiple sources.

## Features
- Scan product barcodes using Waveshare Barcode Scanner Module
- Retrieve nutrition information from USDA FoodData Central database
- Fall back to OpenFoodFacts database for products not in USDA
- Use ChatGPT for AI-based nutrition estimation for products not found in databases
- Process and standardize nutrition data across different sources

## Hardware Requirements
- Raspberry Pi 5
- Waveshare GW-Barcode Scanner Module (connects via USB)

## Software Dependencies
- Python 3.x
- pyserial
- requests
- openai (v0.28.0)
- python-dotenv

## API Keys Required
This module requires API keys for external services:
- USDA FoodData Central API key: https://fdc.nal.usda.gov/api-key-signup.html
- OpenAI API key: https://platform.openai.com/api-keys

API keys should be stored in a `.env` file in the home directory. The keys will be available immediately after registration on these websites.

## Files
The module contains the following files:
- `main.py`: Entry point that initializes components and runs the main scanning loop
- `config.py`: Configuration settings and API key management
- `barcode_scanner.py`: Interface with the Waveshare barcode scanner
- `nutrition_api.py`: Handle nutrition data retrieval from all sources

## How It Works
The module follows a three-tier approach to nutrition data retrieval:
1. Primary: USDA database lookup via API
2. Secondary: OpenFoodFacts database lookup
3. Fallback: ChatGPT-based estimation for products not found in databases

It can handle both barcoded products and products without barcodes (by entering the product name manually).

## Integration Points
This module will integrate with:
- UI & Data Visualization component
- BLE Scale Integration component
- AI-Based Food Recognition component

## Usage (Basic Example)

```python
# Initialize the scanner and nutrition API
scanner = BarcodeScanner()
scanner.connect()
nutrition_api = NutritionAPI()

# Scan a barcode and get nutrition data
barcode = scanner.read_barcode()
nutrition_data = nutrition_api.get_nutrition_data(barcode)

# Access nutrition information
if nutrition_data:
    product_name = nutrition_data.get('name')
    calories = nutrition_data.get('calories')
    protein = nutrition_data.get('protein_g')
    # etc.
```
## Setup Instructions
To set up this module:

1. Install required Python packages:
```bash
pip install pyserial requests python-dotenv openai==0.28.0
```
2. Create a `.env` file in your home directory:
```bash
nano ~/.env
```
3. Add your API keys to the `.env` file:
USDA_API_KEY=your_usda_api_key_here
OPENAI_API_KEY=your_openai_api_key_here

Connect the Waveshare barcode scanner to a USB port on the Raspberry Pi
Run the main application:
python main.py

## Barcode Scanner Compatibility
This implementation is optimized for the Waveshare GW-Barcode Scanner Module. The scanner is detected as "Hangzhou Worlde USBScn Module" in the USB device list.

## Future Enhancements
Potential future improvements include:
- Camera-based barcode scanning using Raspberry Pi camera or PiCar-X camera
- Local caching of previously scanned products
- Improved serving size and weight conversion
- Addition of allergen and ingredient information

## Status
This module is complete and functioning as designed. All required files are now available.

## Team Member
Implemented by: Mohammad Tamim
