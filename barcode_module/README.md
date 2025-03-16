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
- (Optional) PiCar-X camera for image-based barcode scanning

## Software Dependencies
- Python 3.x
- pyserial
- requests
- openai (v0.28.0)
- python-dotenv
- (Optional) pyzbar and opencv-python for camera functionality

## API Keys Required
This module requires API keys for external services:
- USDA FoodData Central API key
- OpenAI API key

API keys should be stored in a `.env` file in the home directory.

## Files (Coming Soon)
The module will contain the following files:
- `main.py`: Entry point that initializes components and runs the main scanning loop
- `config.py`: Configuration settings and API key management
- `barcode_scanner.py`: Interface with the Waveshare barcode scanner
- `nutrition_api.py`: Handle nutrition data retrieval from all sources
- `camera_scanner.py` (optional): Camera-based barcode scanning

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
Full setup instructions and implementation files will be added soon. The setup will involve:
1. Installing required Python packages
2. Configuring API keys
3. Setting up the barcode scanner
4. Testing the system with various products

## Status
This module is complete and functioning as designed. Implementation files will be uploaded incrementally, starting with configuration and main component files.

## Team Member
Implemented by: Mohammad Tamim
