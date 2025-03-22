import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get API keys from environment variables
USDA_API_KEY = os.getenv("USDA_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Scanner configuration - using keyboard mode
SCANNER_AS_KEYBOARD = True