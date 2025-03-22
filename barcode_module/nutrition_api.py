import requests
import json
import openai
from config import USDA_API_KEY, OPENAI_API_KEY

openai.api_key = OPENAI_API_KEY

class NutritionAPI:
    def __init__(self):
        self.usda_base_url = "https://api.nal.usda.gov/fdc/v1"
    
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
            response = requests.get(search_url, params=params)
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
                    detail_response = requests.get(detail_url, params=detail_params)
                    if detail_response.status_code == 200:
                        food_data = detail_response.json()
                        # Process the nutrition data into a standardized format
                        return self._process_usda_data(food_data)
            
            print("Product not found in USDA database")
            return None
            
        except Exception as e:
            print(f"Error fetching nutrition data from USDA: {e}")
            return None
    
    def get_nutrition_from_openfoodfacts(self, barcode):
        """Fetch nutrition data from OpenFoodFacts API using the barcode"""
        try:
            print(f"Trying OpenFoodFacts for barcode: {barcode}")
            openfoodfacts_url = f"https://world.openfoodfacts.org/api/v0/product/{barcode}.json"
            response = requests.get(openfoodfacts_url)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 1:  # Product found
                    # Process the nutrition data into a standardized format
                    return self._process_openfoodfacts_data(data['product'])
            
            print("Product not found in OpenFoodFacts database")
            return None
            
        except Exception as e:
            print(f"Error fetching nutrition data from OpenFoodFacts: {e}")
            return None
    
    def get_nutrition_from_chatgpt(self, product_description):
        """Use ChatGPT to estimate nutrition for products not found in databases"""
        if not OPENAI_API_KEY:
            print("OpenAI API key not found. Please check your .env file.")
            return None
        
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a nutritionist assistant that provides accurate nutrition information in JSON format."},
                    {"role": "user", "content": f"""
                    Provide nutrition information for the following food item in JSON format:
                    {product_description}
                    
                    Return the data as a structured JSON with these fields:
                    - name: product name
                    - serving_size: standard serving size (in grams or milliliters)
                    - calories: total calories per serving
                    - protein_g: protein in grams per serving
                    - carbs_g: carbohydrates in grams per serving
                    - fat_g: total fat in grams per serving
                    - sugar_g: sugar in grams per serving
                    - fiber_g: fiber in grams per serving
                    - sodium_mg: sodium in milligrams per serving
                    
                    Only return the JSON with no explanation or additional text.
                    """}
                ],
                temperature=0.3,  # Lower temperature for more consistent results
            )
            
            # Extract the response content
            nutrition_estimate = response.choices[0].message.content
            
            # Try to parse as JSON
            try:
                json_data = json.loads(nutrition_estimate)
                # Explicitly set the source to ChatGPT
                json_data['source'] = 'ChatGPT'
                return json_data
            except json.JSONDecodeError:
                print("Error parsing ChatGPT response as JSON")
                print(f"Raw response: {nutrition_estimate}")
                return None
            
        except Exception as e:
            print(f"Error getting nutrition estimate from ChatGPT: {e}")
            return None
    
    def get_nutrition_data(self, barcode, product_name=None):
        """Try multiple sources to get nutrition data for a barcode"""
        # First try USDA
        nutrition_data = self.get_nutrition_from_usda(barcode)
        if nutrition_data:
            nutrition_data['source'] = 'USDA'
            return nutrition_data
        
        # Then try OpenFoodFacts
        nutrition_data = self.get_nutrition_from_openfoodfacts(barcode)
        if nutrition_data:
            nutrition_data['source'] = 'OpenFoodFacts'
            return nutrition_data
        
        # If product name is provided, try ChatGPT as a last resort
        if product_name:
            print(f"Trying ChatGPT for: {product_name}")
            nutrition_data = self.get_nutrition_from_chatgpt(product_name)
            if nutrition_data:
                nutrition_data['source'] = 'ChatGPT'
                return nutrition_data
        
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