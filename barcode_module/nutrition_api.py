import requests
import json
import openai
import time
import base64
import re
from config import USDA_API_KEY, OPENAI_API_KEY

openai.api_key = OPENAI_API_KEY

class NutritionAPI:
    def __init__(self):
        self.usda_base_url = "https://api.nal.usda.gov/fdc/v1"
        self.cache = {}  # Simple in-memory cache
        self.api_key = OPENAI_API_KEY
    
    def identify_food(self, image_path=None, image_bytes=None):
        """
        Identify food in an image using OpenAI's Vision API
        Returns: {"status": "success", "food_name": "Banana"} or error dict
        """
        try:
            # If no API key, return mock data
            if not self.api_key:
                print("No API key - using mock data")
                return {"status": "success", "food_name": "Unknown Food"}
                
            # Prepare image data
            if image_path and not image_bytes:
                with open(image_path, "rb") as f:
                    image_bytes = f.read()
                    
            # Convert to base64 for API
            base64_image = base64.b64encode(image_bytes).decode("utf-8")
            
            # Prepare request to OpenAI API
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            
            # Use the current up-to-date model for Vision tasks (as of 2025)
            # UPDATED: Use gpt-4o which has vision capabilities instead of deprecated model
            payload = {
                "model": "gpt-4o",
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a precise food recognition assistant. Identify the exact food item in the image with high specificity. Include brand name if visible. Additionally, estimate the portion size or weight if possible."
                    },
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "What specific food item is shown in this image? Be precise and detailed. Include brand name if visible. Also, if possible, estimate the portion size."},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                "max_tokens": 150  # Increased max tokens to allow for portion size estimation
            }
            
            # Make API request
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=payload
            )
            
            if response.status_code == 200:
                result = response.json()
                food_description = result["choices"][0]["message"]["content"].strip()
                print(f"Response from vision API: {food_description}")
                
                # Extract food name and portion info
                food_info = self._parse_food_description(food_description)
                
                return {
                    "status": "success", 
                    "food_name": food_info["food_name"],
                    "portion_estimate": food_info.get("portion_estimate", None),
                    "raw_description": food_description
                }
            else:
                print(f"API error: {response.status_code} - {response.text}")
                return {"status": "error", "message": f"API error: {response.status_code}"}
                
        except Exception as e:
            print(f"Error identifying food: {e}")
            return {"status": "error", "message": str(e)}
    
    def _parse_food_description(self, description):
        """Parse food description to extract food name and portion estimate"""
        
        # Default result
        result = {
            "food_name": description
        }
        
        # Try to identify portion information
        portion_patterns = [
            r'portion size:?\s*([\w\s\d.]+(?:grams|gram|g|oz|ounce|ml|cups|cup|tbsp|tsp|piece|pieces|slice|slices))',
            r'estimated\s+(?:portion|weight|size):?\s*([\w\s\d.]+(?:grams|gram|g|oz|ounce|ml|cups|cup|tbsp|tsp|piece|pieces|slice|slices))',
            r'approximately\s*([\d.]+\s*(?:grams|gram|g|oz|ounce|ml|cups|cup|tbsp|tsp|piece|pieces|slice|slices))'
        ]
        
        # Try each pattern
        for pattern in portion_patterns:
            match = re.search(pattern, description, re.IGNORECASE)
            if match:
                result["portion_estimate"] = match.group(1).strip()
                # Remove portion info from food name
                description = re.sub(pattern, '', description, flags=re.IGNORECASE).strip()
                break
        
        # Clean up food name (remove any "This is a" prefixes and similar)
        food_name = re.sub(r'^(this is|i see|the image shows|it appears to be)\s+a\s+', '', description, flags=re.IGNORECASE)
        food_name = re.sub(r'^a\s+', '', food_name, flags=re.IGNORECASE)
        
        # Further clean punctuation and extra whitespace
        food_name = re.sub(r'\s+', ' ', food_name).strip('.,; ')
        
        result["food_name"] = food_name
        
        return result
    
    def get_nutrition_from_usda(self, barcode):
        """Fetch nutrition data from USDA API using the barcode"""
        if not USDA_API_KEY:
            print("USDA API key not found. Please check your .env file.")
            return None
        
        # First search for the product by barcode
        search_url = f"{self.usda_base_url}/foods/search"
        params = {
            "api_key": USDA_API_KEY,
            "query": barcode,
            "dataType": ["Branded"]
        }
        
        try:
            response = requests.get(search_url, params=params, timeout=5)  # 5-second timeout
            if response.status_code == 200:
                data = response.json()
                if data.get('totalHits', 0) > 0:
                    # Get the first match
                    food = data['foods'][0]
                    food_id = food['fdcId']
                    
                    # Get detailed nutrition information
                    detail_url = f"{self.usda_base_url}/food/{food_id}"
                    detail_params = {
                        "api_key": USDA_API_KEY
                    }
                    detail_response = requests.get(detail_url, params=detail_params, timeout=5)
                    if detail_response.status_code == 200:
                        food_data = detail_response.json()
                        # Process the nutrition data into a standardized format
                        return self._process_usda_data(food_data)
            
            print("Product not found in USDA database")
            return None
            
        except requests.exceptions.Timeout:
            print("USDA API request timed out")
            return None
        except Exception as e:
            print(f"Error fetching nutrition data from USDA: {e}")
            return None
    
    def get_nutrition_from_openfoodfacts(self, barcode):
        """Fetch nutrition data from OpenFoodFacts API using the barcode"""
        try:
            print(f"Trying OpenFoodFacts for barcode: {barcode}")
            openfoodfacts_url = f"https://world.openfoodfacts.org/api/v0/product/{barcode}.json"
            response = requests.get(openfoodfacts_url, timeout=5)  # 5-second timeout
            
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 1:  # Product found
                    # Process the nutrition data into a standardized format
                    return self._process_openfoodfacts_data(data['product'])
            
            print("Product not found in OpenFoodFacts database")
            return None
            
        except requests.exceptions.Timeout:
            print("OpenFoodFacts API request timed out")
            return None
        except Exception as e:
            print(f"Error fetching nutrition data from OpenFoodFacts: {e}")
            return None
    
    def get_nutrition_from_chatgpt(self, product_description, portion_estimate=None):
        """Use ChatGPT to estimate nutrition for products not found in databases"""
        if not self.api_key:
            print("OpenAI API key not found. Please check your .env file.")
            return None
        
        try:
            # Using the updated client approach for newer OpenAI API version
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            
            # Add portion information to the prompt if available
            portion_text = ""
            if portion_estimate:
                portion_text = f"The estimated portion size is: {portion_estimate}. Please adjust the nutrition values accordingly."
            
            payload = {
                "model": "gpt-4",  # Using standard gpt-4 model
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a nutritionist assistant that provides accurate nutrition information. Only reject inputs that are clearly not food items (like random strings, numbers, or nonsense words). Respond with valid JSON."
                    },
                    {
                        "role": "user",
                        "content": f"""
                        Analyze this input: "{product_description}"
                        {portion_text}
                        
                        If this is clearly NOT a food item (like random characters, nonsense words, or obviously non-food), respond with:
                        {{
                            "is_food": false
                        }}
                        
                        For ANY input that could reasonably be a food item or dish, even if unusual or you're not familiar with it, provide estimated nutrition information in this exact JSON format:
                        {{
                            "name": "product name",
                            "serving_size": "standard serving size (in grams or milliliters, or the portion size provided)",
                            "calories": total calories per serving (number),
                            "protein_g": protein in grams per serving (number),
                            "carbs_g": carbohydrates in grams per serving (number),
                            "fat_g": total fat in grams per serving (number),
                            "sugar_g": sugar in grams per serving (number),
                            "fiber_g": fiber in grams per serving (number),
                            "sodium_mg": sodium in milligrams per serving (number)
                        }}
                        
                        Make sure to format your response as valid JSON with NO additional text or explanation.
                        """
                    }
                ],
                "temperature": 0.3  # Lower temperature for more consistent results
            }
            
            # Make API request
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=10  # 10-second timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                nutrition_estimate = result["choices"][0]["message"]["content"].strip()
                
                # Try to parse as JSON
                try:
                    json_data = json.loads(nutrition_estimate)
                    
                    # Check if the input is not a food item
                    if json_data.get('is_food') is False:
                        print(f"'{product_description}' is not recognized as a valid food item")
                        return None
                    
                    # Explicitly set the source to ChatGPT
                    json_data['source'] = 'ChatGPT (GPT-4)'
                    
                    # Add the portion estimate if it was provided
                    if portion_estimate:
                        json_data['portion_estimate'] = portion_estimate
                        
                    return json_data
                except json.JSONDecodeError:
                    print("Error parsing ChatGPT response as JSON")
                    print(f"Raw response: {nutrition_estimate}")
                    return None
            else:
                print(f"API error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"Error getting nutrition estimate from ChatGPT: {e}")
            return None
    
    def get_nutrition_data(self, barcode, product_name=None):
        """Try multiple sources to get nutrition data for a barcode"""
        # Check cache first
        if barcode in self.cache:
            print(f"Cache hit for barcode: {barcode}")
            return self.cache[barcode]
        
        start_time = time.time()
        
        # First try USDA
        print(f"Trying USDA for barcode: {barcode}")
        nutrition_data = self.get_nutrition_from_usda(barcode)
        if nutrition_data:
            print(f"USDA lookup took {time.time() - start_time:.2f} seconds")
            nutrition_data['source'] = 'USDA'
            self.cache[barcode] = nutrition_data
            return nutrition_data
        
        print(f"USDA lookup failed after {time.time() - start_time:.2f} seconds")
        usda_time = time.time()
        
        # Then try OpenFoodFacts
        print(f"Trying OpenFoodFacts for barcode: {barcode}")
        nutrition_data = self.get_nutrition_from_openfoodfacts(barcode)
        if nutrition_data:
            print(f"OpenFoodFacts lookup took {time.time() - usda_time:.2f} seconds")
            nutrition_data['source'] = 'OpenFoodFacts'
            self.cache[barcode] = nutrition_data
            return nutrition_data
        
        print(f"OpenFoodFacts lookup failed after {time.time() - usda_time:.2f} seconds")
        off_time = time.time()
        
        # If product name is provided, try ChatGPT as a last resort
        if product_name:
            print(f"Trying ChatGPT for: {product_name}")
            nutrition_data = self.get_nutrition_from_chatgpt(product_name)
            if nutrition_data:
                print(f"ChatGPT lookup took {time.time() - off_time:.2f} seconds")
                nutrition_data['source'] = 'ChatGPT (GPT-4)'
                self.cache[barcode] = nutrition_data
                return nutrition_data
        
        print(f"Total lookup time: {time.time() - start_time:.2f} seconds")
        return None
    
    def _process_usda_data(self, data):
        """Process USDA API data into a standardized format"""
        result = {
            'name': data.get('description', 'Unknown Product'),
            'serving_size': 'Unknown',
            'calories': 0,
            'protein_g': 0,
            'carbs_g': 0,
            'fat_g': 0,
            'sugar_g': 0,
            'fiber_g': 0,
            'sodium_mg': 0
        }
        
        # Extract serving size
        for portion in data.get('foodPortions', []):
            if 'gramWeight' in portion:
                result['serving_size'] = f"{portion['gramWeight']}g"
                break
        
        # Extract nutrients
        for nutrient in data.get('foodNutrients', []):
            nutrient_name = nutrient.get('nutrient', {}).get('name', '').lower()
            amount = nutrient.get('amount', 0)
            
            if 'energy' in nutrient_name and 'kcal' in nutrient_name:
                result['calories'] = amount
            elif 'protein' in nutrient_name:
                result['protein_g'] = amount
            elif 'carbohydrate' in nutrient_name and 'total' in nutrient_name:
                result['carbs_g'] = amount
            elif 'fat' in nutrient_name and ('total' in nutrient_name or len(nutrient_name.split()) < 3):
                result['fat_g'] = amount
            elif 'sugars' in nutrient_name:
                result['sugar_g'] = amount
            elif 'fiber' in nutrient_name:
                result['fiber_g'] = amount
            elif 'sodium' in nutrient_name:
                result['sodium_mg'] = amount
        
        return result
    
    def _process_openfoodfacts_data(self, data):
        """Process OpenFoodFacts API data into a standardized format"""
        result = {
            'name': data.get('product_name', 'Unknown Product'),
            'serving_size': data.get('serving_size', 'Unknown'),
            'calories': 0,
            'protein_g': 0,
            'carbs_g': 0,
            'fat_g': 0,
            'sugar_g': 0,
            'fiber_g': 0,
            'sodium_mg': 0
        }
        
        # Extract nutrients from nutriments
        nutriments = data.get('nutriments', {})
        
        # Convert per_serving or per_100g values to per serving values
        result['calories'] = nutriments.get('energy-kcal_serving', nutriments.get('energy-kcal', 0))
        result['protein_g'] = nutriments.get('proteins_serving', nutriments.get('proteins', 0))
        result['carbs_g'] = nutriments.get('carbohydrates_serving', nutriments.get('carbohydrates', 0))
        result['fat_g'] = nutriments.get('fat_serving', nutriments.get('fat', 0))
        result['sugar_g'] = nutriments.get('sugars_serving', nutriments.get('sugars', 0))
        result['fiber_g'] = nutriments.get('fiber_serving', nutriments.get('fiber', 0))
        result['sodium_mg'] = nutriments.get('sodium_serving', nutriments.get('sodium', 0))
        
        return result
