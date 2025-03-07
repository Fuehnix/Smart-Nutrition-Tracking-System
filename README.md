# Smart-Nutrition-Tracking-System
## Motivation
Maintaining a healthy diet is challenging because most food tracking systems are manual, time-consuming, and error-prone. Many calorie-counting apps require users to enter food items manually, making the process tedious and unreliable. Additionally, kitchen scales only measure weight without providing nutritional information.

Our project aims to automate nutrition tracking by integrating:
- A Bluetooth-enabled kitchen scale for real-time weight measurement.
- Barcode scanning for quick lookup of packaged food nutrition facts.
- AI-based food recognition for non-packaged foods like fruits, vegetables, and meals.
- ChatGPT-based estimation when users are dining out and can’t use a scale.
- A user-friendly interface to display and analyze daily intake.
- (Stretch Feature) Potential integration with a smart body scale to analyze weight trends alongside nutrition intake
- This system will empower individuals to track their nutrition effortlessly, benefiting:
- Health-conscious individuals who want precise calorie & nutrient tracking.
- People with dietary restrictions (diabetes, hypertension, etc.).
- Fitness enthusiasts who need accurate macronutrient monitoring.
  
By removing the friction in food tracking, we make healthy eating easier and more accessible.

## Project Objectives
Core Features:
- Barcode Scanning & Nutrition Lookup
- Scan barcodes to fetch nutrition data from an API or ChatGPT.
- AI-Based Food Recognition
- Identify non-packaged food from images using an AI model.
- ChatGPT-Based Estimation for Dining Out
- Estimate nutrition values for restaurant meals via natural language input.
- Bluetooth Kitchen Scale Integration
- Retrieve weight data via BLE from a kitchen scale to a Raspberry Pi 5.
- User Interface & Data Visualization
- Log daily intake, view nutritional breakdown (calories, protein, fat, carbs, sodium, etc.).

Stretch Features (if time allows):
- Recipe suggestions based on food data.
- Entertainment features (e.g., watching videos on a built-in screen).
- BLE Body Scale Integration
- Retrieve weight and body composition data via BLE from a body scale (eg. Xiaomi)
- Analyze weight trends alongside nutritional intake

## Parts list (So far):
- [Barcode scanner module ($42)](https://www.amazon.com/dp/B07P3GD3XV?ref=ppx_yo2ov_dt_b_fed_asin_title)
- [Open Source Bluetooth kitchen scale ($89)](https://decentespresso.com/decentscale)
- [Raspberry Pi Camera (any / $14)](https://www.amazon.com/dp/B01ER2SKFS?ref_=ppx_hzsearch_conn_dt_b_fed_asin_title_1_)
- [Raspberry Pi 4 8gb (recommended, any raspberry pi 4 or 5 will likely work)($84)](https://www.amazon.com/Raspberry-Pi-Computer-Suitable-Workstation/dp/B0899VXM8F)
- Touch Screen (any):
  - [7" or 10" ROADCOM Touchscreen with case ($79.99)](https://www.amazon.com/ROADOM-Raspberry-Responsive-Compatible-Versatile/dp/B0CJNHY3X3?crid=2GB5T80V5TO4X&th=1)
