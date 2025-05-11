from flask import Flask, render_template, request, redirect, url_for, jsonify
import os
import time
import json
import random
from datetime import datetime

# Import custom modules
import sys
sys.path.append('../image_recognition')
sys.path.append('../scale_module')
sys.path.append('../barcode_module')

try:
    from nutrition_api import NutritionAPI
    nutrition_api_available = True
    nutrition_api = NutritionAPI()
    print("Nutrition API module available")
except ImportError:
    print("Warning: NutritionAPI module not available")
    nutrition_api_available = False
    nutrition_api = None

# Global variables for scale integration
scale_integration = None
scale_integration_available = False
decent_scale = None
decent_scale_available = False

# Try to import the ScaleIntegration module
try:
    from scale_integration import ScaleIntegration
    scale_integration = ScaleIntegration()
    scale_integration_available = True
    print("Scale Integration module available")
except ImportError:
    print("Warning: ScaleIntegration module not available")
    scale_integration_available = False

# Try direct DecentScale import as a fallback
try:
    from decent_scale import DecentScale
    decent_scale = DecentScale()
    decent_scale_available = True
    print("Decent Scale directly available")
except ImportError as e:
    print(f"Warning: DecentScale direct import failed: {e}")
    decent_scale_available = False
except Exception as e:
    print(f"Warning: DecentScale initialization failed: {e}")
    decent_scale_available = False

# Use direct import of local SimpleCamera module
from simple_camera import SimpleCamera
camera_feed = SimpleCamera()
camera_feed_available = True
print("Camera module available using command-line tools")

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'smartnutrition2025'

# Mock data for testing if real modules are not available
scanned_items = []

# Routes
@app.route('/')
def index():
    return render_template('index.html', scanned_items=scanned_items)

@app.route('/scan')
def scan():
    return render_template('scan.html')

@app.route('/daily_summary')
def daily_summary():
    # Calculate totals
    totals = {
        'calories': sum(item.get('calories', 0) for item in scanned_items),
        'protein_g': sum(item.get('protein_g', 0) for item in scanned_items),
        'carbs_g': sum(item.get('carbs_g', 0) for item in scanned_items),
        'fat_g': sum(item.get('fat_g', 0) for item in scanned_items),
        'sugar_g': sum(item.get('sugar_g', 0) for item in scanned_items),
        'fiber_g': sum(item.get('fiber_g', 0) for item in scanned_items),
        'sodium_mg': sum(item.get('sodium_mg', 0) for item in scanned_items)
    }
    return render_template('daily_summary.html', items=scanned_items, totals=totals)

@app.route('/history')
def history():
    return render_template('history.html', scanned_items=scanned_items)

@app.route('/nutrition_details/<int:item_id>')
def nutrition_details(item_id):
    if 0 <= item_id < len(scanned_items):
        return render_template('nutrition_details.html', item=scanned_items[item_id])
    return redirect(url_for('index'))

@app.route('/body_composition_page')
def body_composition_page():
    return render_template('body_composition.html')

# New API endpoint to get item details by ID
@app.route('/api/item/<int:item_id>', methods=['GET'])
def get_item_details(item_id):
    if 0 <= item_id < len(scanned_items):
        return jsonify(scanned_items[item_id])
    return jsonify({"error": "Item not found"}), 404

# New API endpoint to search for an item by barcode
@app.route('/api/search_barcode/<barcode>', methods=['GET'])
def search_barcode(barcode):
    if nutrition_api and nutrition_api_available:
        nutrition_data = nutrition_api.get_nutrition_data(barcode)
        if nutrition_data:
            return jsonify({
                "status": "success",
                "data": nutrition_data
            })
    
    # If no data found or no API available
    return jsonify({
        "status": "error",
        "message": "Barcode not found in database"
    })

# API endpoints
@app.route('/api/trigger_scale', methods=['GET'])
def trigger_scale():
    # Access the global variables
    global scale_integration, scale_integration_available, decent_scale, decent_scale_available
    
    # First try using the ScaleIntegration if available
    if scale_integration and scale_integration_available:
        try:
            print("Trying full scale integration...")
            weight_data = scale_integration.get_kitchen_scale_weight()
            print(f"Got weight data from scale integration: {weight_data}")
            return jsonify(weight_data)
        except Exception as e:
            print(f"Error using ScaleIntegration: {e}")
            # Fall through to next option if this fails
    
    # Then try direct Decent scale if available
    if decent_scale and decent_scale_available:
        try:
            print("Trying to get weight from Decent scale directly...")
            weight_data = decent_scale.get_weight()
            if weight_data and 'weight' in weight_data and 'unit' in weight_data:
                print(f"Successfully got weight from Decent scale directly: {weight_data}")
                return jsonify({
                    "status": "success",
                    "weight": weight_data.get('weight', 0),
                    "unit": weight_data.get('unit', 'g'),
                    "source": "Decent Scale Direct"
                })
            else:
                print("Failed to get valid data from Decent scale")
        except Exception as e:
            print(f"Error using direct Decent scale: {e}")
            # Fall through to mock data if this fails
    
    # Fall back to mock data if nothing else works
    print("Using mock weight data")
    return jsonify({
        "status": "success",
        "weight": round(random.uniform(100, 250), 1),
        "unit": "g",
        "source": "Mock Data"
    })

@app.route('/api/body_composition', methods=['GET'])
def get_body_composition():
    # Get parameters
    height = request.args.get('height', type=float)
    age = request.args.get('age', type=int)
    sex = request.args.get('sex', 'Male')
    country = request.args.get('country', 'USA')
    
    if scale_integration and scale_integration_available:
        try:
            composition_data = scale_integration.get_body_composition()
            
            # Debug logging
            print(f"Scale data structure: {composition_data}")
            
            # Fix the data extraction - handle multiple levels of nesting
            if composition_data.get('status') == 'success':
                # We might have several levels of nesting, let's unwrap them all
                scale_data = composition_data.get('data', {})
                
                # Keep unwrapping nested 'data' fields until we find the actual data
                while isinstance(scale_data, dict) and 'data' in scale_data and isinstance(scale_data['data'], dict):
                    scale_data = scale_data['data']
                
                # Extract and validate the weight
                weight = scale_data.get('weight')
                print(f"Extracted weight: {weight}")
                
                # Validate weight is reasonable - but don't automatically assume it's wrong
                # Some Xiaomi scales have a direct weight display that should be trusted
                if weight is None or weight <= 0:
                    print(f"Weight value unreasonable: {weight}, using mock data instead")
                    # Use mock data
                    mock_data = {
                        "weight": 172.5 if sex == "Male" else 145.3,
                        "unit": "lb",
                        "bmi": 24.3 if sex == "Male" else 23.1,
                        "body_fat_percentage": 18.5 if sex == "Male" else 24.2,
                        "muscle_mass": 140.2 if sex == "Male" else 110.5,
                        "bone_mass": 8.1 if sex == "Male" else 6.8,
                        "body_water_percentage": 62.5 if sex == "Male" else 58.3,
                        "protein_percentage": 16.8 if sex == "Male" else 15.4,
                        "basal_metabolism": 1780 if sex == "Male" else 1520,
                        "visceral_fat": 9 if sex == "Male" else 7,
                        "metabolic_age": 28 if sex == "Male" else 30,
                        "ideal_weight": 165.0 if sex == "Male" else 135.0,
                        "life_expectancy": 83.4 if sex == "Male" else 86.2,
                        "fromMockData": True
                    }
                    return jsonify({"status": "success", "data": mock_data})
                else:
                    # Make sure every field needed by the UI is available
                    # Add the fromMockData flag to indicate real data
                    scale_data['fromMockData'] = False
                    
                    # Ensure all required fields are present
                    required_fields = [
                        'unit', 'bmi', 'body_fat_percentage', 'muscle_mass', 'bone_mass',
                        'body_water_percentage', 'protein_percentage', 'basal_metabolism',
                        'visceral_fat', 'metabolic_age', 'ideal_weight', 'life_expectancy'
                    ]
                    
                    for field in required_fields:
                        if field not in scale_data:
                            if field == 'unit' and 'weight' in scale_data:
                                scale_data[field] = 'lb'  # Default unit
                    
                    # Log final data being sent to UI
                    print(f"Sending body composition data to UI: {scale_data}")
                    
                    # Use the actual scale data
                    return jsonify({"status": "success", "data": scale_data})
            
            # If we got this far, something went wrong
            return jsonify(composition_data)
        except Exception as e:
            print(f"Error in body composition: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({"status": "error", "message": str(e)})
    else:
        # Mock data for testing if real modules are not available
        mock_data = {
            "status": "success",
            "data": {
                "weight": 172.5 if sex == "Male" else 145.3,
                "unit": "lb",
                "bmi": 24.3 if sex == "Male" else 23.1,
                "body_fat_percentage": 18.5 if sex == "Male" else 24.2,
                "muscle_mass": 140.2 if sex == "Male" else 110.5,
                "bone_mass": 8.1 if sex == "Male" else 6.8,
                "body_water_percentage": 62.5 if sex == "Male" else 58.3,
                "protein_percentage": 16.8 if sex == "Male" else 15.4,
                "basal_metabolism": 1780 if sex == "Male" else 1520,
                "visceral_fat": 9 if sex == "Male" else 7,
                "metabolic_age": 28 if sex == "Male" else 30,
                "ideal_weight": 165.0 if sex == "Male" else 135.0,
                "life_expectancy": 83.4 if sex == "Male" else 86.2,
                "fromMockData": True
            }
        }
        return jsonify(mock_data)

@app.route('/api/daily_totals', methods=['GET'])
def get_daily_totals():
    totals = {
        'calories': sum(item.get('calories', 0) for item in scanned_items),
        'protein_g': sum(item.get('protein_g', 0) for item in scanned_items),
        'carbs_g': sum(item.get('carbs_g', 0) for item in scanned_items),
        'fat_g': sum(item.get('fat_g', 0) for item in scanned_items),
        'sugar_g': sum(item.get('sugar_g', 0) for item in scanned_items),
        'fiber_g': sum(item.get('fiber_g', 0) for item in scanned_items),
        'sodium_mg': sum(item.get('sodium_mg', 0) for item in scanned_items)
    }
    return jsonify(totals)

@app.route('/api/update_live_view', methods=['GET'])
def update_live_view():
    """Route to update the live camera view"""
    if camera_feed and camera_feed_available:
        try:
            success, image_path = camera_feed.update_live_view()
            if success:
                return jsonify({
                    "status": "success",
                    "image_path": image_path
                })
            else:
                return jsonify({
                    "status": "error",
                    "message": image_path
                })
        except Exception as e:
            return jsonify({
                "status": "error",
                "message": str(e)
            })
    else:
        # Return a mock image path
        return jsonify({
            "status": "success",
            "image_path": "/static/img/demo_food.jpg"
        })

@app.route('/api/trigger_camera', methods=['GET'])
def trigger_camera():
    if camera_feed and camera_feed_available and nutrition_api and nutrition_api_available:
        try:
            # Capture image
            success, capture_path = camera_feed.capture_image()
            if not success:
                return jsonify({
                    "status": "error",
                    "message": f"Failed to capture image: {capture_path}"
                })
            
            # Use nutrition_api to identify food
            food_result = nutrition_api.identify_food(image_path=capture_path)
            
            if food_result and food_result.get("status") == "success":
                food_name = food_result.get("food_name", "Unknown food")
                print(f"Identified food: {food_name}")
                
                # Use nutrition_api to get nutrition data
                nutrition_data = nutrition_api.get_nutrition_from_chatgpt(food_name)
                
                # If nutrition data is retrieved, add to scanned items
                if nutrition_data:
                    # Add timestamp
                    now = datetime.now()
                    nutrition_data['timestamp'] = now.strftime("%Y-%m-%d %H:%M:%S")
                    
                    # Add to scanned items
                    scanned_items.insert(0, nutrition_data)
                    
                    # Prepare redirect URL
                    redirect_url = url_for('nutrition_details', item_id=0)
                else:
                    redirect_url = url_for('scan', food=food_name)
                
                # The frontend will handle showing the weighing option dialog
                return jsonify({
                    "status": "success",
                    "food_name": food_name,
                    "image_url": f"/{capture_path}",
                    "redirect_url": redirect_url,
                    "has_nutrition_data": nutrition_data is not None
                })
            else:
                return jsonify({
                    "status": "error",
                    "message": "Could not identify food in image",
                    "image_url": f"/{capture_path}"
                })
        except Exception as e:
            return jsonify({
                "status": "error",
                "message": f"Camera error: {str(e)}"
            })
    else:
        # Mock data for testing
        mock_foods = ["Apple", "Banana", "Chicken Breast", "Salad", "Pizza", "Hamburger"]
        mock_food = random.choice(mock_foods)
        
        # Add mock nutrition data
        nutrition_data = {
            "name": mock_food,
            "serving_size": "100g",
            "calories": random.randint(50, 400),
            "protein_g": round(random.uniform(2, 25), 1),
            "carbs_g": round(random.uniform(5, 40), 1),
            "fat_g": round(random.uniform(0, 20), 1),
            "sugar_g": round(random.uniform(0, 15), 1),
            "fiber_g": round(random.uniform(0, 8), 1),
            "sodium_mg": random.randint(10, 800),
            "source": "Demo Data",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Add to scanned items
        scanned_items.insert(0, nutrition_data)
        
        return jsonify({
            "status": "success",
            "food_name": mock_food,
            "image_url": "/static/img/demo_food.jpg",
            "redirect_url": url_for('nutrition_details', item_id=0),
            "has_nutrition_data": True
        })

@app.route('/apply_weight', methods=['GET'])
def apply_weight():
    name = request.args.get('name')
    weight = request.args.get('weight', type=float)
    unit = request.args.get('unit')
    
    if not name or weight is None:
        return redirect(url_for('scan', error="Missing food name or weight"))
    
    # If nutrition API is available, get nutrition data
    nutrition_data = None
    if nutrition_api and nutrition_api_available:
        # First check if this is a barcode
        if name.startswith("Product with barcode:"):
            barcode = name.split(":")[-1].strip()
            nutrition_data = nutrition_api.get_nutrition_data(barcode)
        else:
            nutrition_data = nutrition_api.get_nutrition_from_chatgpt(name)
    
    if nutrition_data is None:
        # Mock data
        nutrition_data = {
            "name": name,
            "serving_size": f"{weight}{unit}",
            "calories": int(weight * 2.5),
            "protein_g": round(weight * 0.1, 1),
            "carbs_g": round(weight * 0.25, 1),
            "fat_g": round(weight * 0.08, 1),
            "sugar_g": round(weight * 0.05, 1),
            "fiber_g": round(weight * 0.03, 1),
            "sodium_mg": int(weight * 5),
            "source": "Weight Adjusted",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    else:
        # Adjust for measured weight
        reference_weight = 100.0  # Assuming 100g reference for ChatGPT estimates
        
        # Try to extract numeric weight from serving size
        current_serving_size = nutrition_data.get("serving_size", "100g")
        serving_match = None
        
        # Try to extract numeric portion from serving size
        import re
        serving_match = re.search(r'(\d+(\.\d+)?)', current_serving_size)
        
        if serving_match:
            reference_weight = float(serving_match.group(1))
        
        # Calculate weight ratio
        weight_ratio = weight / reference_weight
        
        # Update serving size with measured weight
        nutrition_data["serving_size"] = f"{weight}{unit}"
        
        # Adjust nutrient values proportionally
        for key in ["calories", "protein_g", "carbs_g", "fat_g", "sugar_g", "fiber_g", "sodium_mg"]:
            if key in nutrition_data and isinstance(nutrition_data[key], (int, float)):
                if key == "calories":
                    nutrition_data[key] = int(nutrition_data[key] * weight_ratio)
                else:
                    nutrition_data[key] = round(nutrition_data[key] * weight_ratio, 1)
        
        # Add timestamp and update source
        original_source = nutrition_data.get('source', 'Unknown')
        nutrition_data["source"] = f"{original_source} (Weight Adjusted)"
        nutrition_data["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Add to scanned items
    scanned_items.insert(0, nutrition_data)
    
    return redirect(url_for('nutrition_details', item_id=0))

@app.route('/scan', methods=['POST'])
def scan_post():
    barcode_or_name = request.form.get('barcode_or_name')
    
    if not barcode_or_name:
        return redirect(url_for('scan', error="Please enter a barcode or product name"))
    
    # Check if input looks like a barcode
    is_barcode = barcode_or_name.isdigit() and len(barcode_or_name) >= 8
    
    nutrition_data = None
    if nutrition_api and nutrition_api_available:
        if is_barcode:
            nutrition_data = nutrition_api.get_nutrition_data(barcode_or_name)
        else:
            nutrition_data = nutrition_api.get_nutrition_from_chatgpt(barcode_or_name)
    
    if not nutrition_data:
        # Mock data
        nutrition_data = {
            "name": barcode_or_name if not is_barcode else f"Product {barcode_or_name[:4]}",
            "serving_size": "100g",
            "calories": random.randint(100, 400),
            "protein_g": round(random.uniform(5, 25), 1),
            "carbs_g": round(random.uniform(10, 50), 1),
            "fat_g": round(random.uniform(2, 20), 1),
            "sugar_g": round(random.uniform(1, 15), 1),
            "fiber_g": round(random.uniform(0, 8), 1),
            "sodium_mg": random.randint(50, 800),
            "source": "Demo Data",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    
    # Add timestamp if not present
    if 'timestamp' not in nutrition_data:
        nutrition_data['timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Add to scanned items
    scanned_items.insert(0, nutrition_data)
    
    # For AJAX barcode scanning, return a JSON response
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({
            "status": "success",
            "redirect_url": url_for('nutrition_details', item_id=0),
            "food_name": nutrition_data.get("name", "Unknown Product")
        })
    
    # Regular form submission - redirect to details
    return redirect(url_for('nutrition_details', item_id=0))

# Cleanup resources on exit
def cleanup():
    print("Cleaning up resources...")
    if camera_feed:
        camera_feed.release_camera()

if __name__ == '__main__':
    try:
        # Create necessary directories
        os.makedirs('static/img', exist_ok=True)
        
        # Run the app
        app.run(host='0.0.0.0', debug=True)
    finally:
        cleanup()