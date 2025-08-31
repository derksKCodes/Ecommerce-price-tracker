import re
import json
import logging
from datetime import datetime

def setup_logging(name):
    """Set up logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(f'logs/{name}.log'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(name)

def extract_price(price_str):
    """Extract numeric price from string"""
    if not price_str or price_str == "Not Found":
        return None
        
    try:
        # Remove currency symbols, commas, and other non-numeric characters except decimal point
        cleaned = re.sub(r'[^\d.]', '', str(price_str))
        return float(cleaned)
    except (ValueError, TypeError):
        return None

def extract_discount(discount_str):
    """Extract numeric discount percentage from string"""
    if not discount_str or discount_str == "Not Found":
        return 0
        
    try:
        # Extract numbers from discount string (e.g., "10% OFF" -> 10)
        numbers = re.findall(r'\d+', str(discount_str))
        if numbers:
            return float(numbers[0])
        return 0
    except (ValueError, TypeError):
        return 0

def load_config(config_file):
    """Load configuration from JSON file"""
    try:
        with open(config_file, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading config file {config_file}: {e}")
        return {}

def save_config(config, config_file):
    """Save configuration to JSON file"""
    try:
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=4)
        return True
    except Exception as e:
        print(f"Error saving config file {config_file}: {e}")
        return False

def format_timestamp(timestamp=None):
    """Format timestamp for filenames"""
    if timestamp is None:
        timestamp = datetime.now()
    return timestamp.strftime("%Y%m%d_%H%M%S")

def clean_price(price_str):
    """
    Convert scraped price strings into floats.
    Removes currency symbols, commas, and handles 'Not Found'.
    """
    if not price_str or "Not Found" in price_str:
        return None
    try:
        # Keep only digits and dots
        clean = re.sub(r"[^\d.]", "", price_str)
        return float(clean)
    except Exception:
        return None