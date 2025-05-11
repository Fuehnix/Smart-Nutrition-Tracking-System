import os
import base64
import subprocess
from pathlib import Path
import openai
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

class FoodRecognizer:
    def __init__(self):
        self.last_image_path = Path("static/img/captured.jpg")

    def capture_image(self):
        """Capture an image using libcamera-still and return image bytes"""
        try:
            # Remove old image if exists
            if self.last_image_path.exists():
                self.last_image_path.unlink()

            print("Capturing image with libcamera-still...")
            result = subprocess.run([
                "libcamera-still",
                "-o", str(self.last_image_path),
                "-t", "1000",
                "--width", "640",
                "--height", "480",
                "--nopreview"
            ], check=True)

            if self.last_image_path.exists():
                print(f"Image captured at: {self.last_image_path}")
                with open(self.last_image_path, "rb") as img_file:
                    return img_file.read()
            else:
                print("Image not found after capture.")
                return None

        except subprocess.CalledProcessError as e:
            print(f"libcamera-still failed: {e}")
            return None

    def identify_food(self, image_bytes=None, image_path=None):
        """
        Identify food in an image using OpenAI Vision API
        Returns: {"status": "success", "food_name": "Banana"} or error dict
        """
        try:
            # Capture new image if none provided
            if image_bytes is None and image_path is None:
                image_bytes = self.capture_image()
                if image_bytes is None:
                    return {"status": "error", "message": "Failed to capture image"}

            # If loading from file path
            if image_path and not image_bytes:
                with open(image_path, "rb") as f:
                    image_bytes = f.read()

            # Convert to base64 for OpenAI API
            base64_image = base64.b64encode(image_bytes).decode("utf-8")

            print("Sending image to OpenAI Vision model...")
            response = openai.ChatCompletion.create(
                model="gpt-4o",  
                messages=[
                    {
                        "role": "system",
                        "content": "You are a food recognition assistant. Identify the food in the image."
                    },
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "What food is in this image? Just return the food name."},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=50
            )

            food_name = response.choices[0].message['content'].strip()
            print(f"Detected food: {food_name}")
            return {"status": "success", "food_name": food_name}

        except Exception as e:
            print(f"Error identifying food: {e}")
            return {"status": "error", "message": str(e)}

