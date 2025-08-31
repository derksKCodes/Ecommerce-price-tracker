"""
Setup script for E-commerce Price Tracker
"""
import os
import json
from src.utils import setup_logging

def setup_project():
    """Set up the project structure and default files"""
    logger = setup_logging('setup')
    
    # Create directories
    directories = [
        'config',
        'data/csv',
        'data/json',
        'data/excel',
        'data/charts',
        'logs',
        'src'
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        logger.info(f"Created directory: {directory}")
    
    # Create default config files if they don't exist
    if not os.path.exists('config/products.json'):
        default_products = {
            "amazon": [
                "https://www.amazon.com/dp/B08N5WRWNW",  # Example product
                "https://www.amazon.com/dp/B08N5P7HW6"   # Another example
            ],
            "ebay": [
                "https://www.ebay.com/itm/284003123456",  # Example product
                "https://www.ebay.com/itm/284003123457"   # Another example
            ],
            "aliexpress": [
                "https://www.aliexpress.com/item/4001234567890.html",  # Example product
                "https://www.aliexpress.com/item/4001234567891.html"   # Another example
            ],
            "jumia": [
                "https://www.jumia.com.ng/catalog/product1234567",  # Example product
                "https://www.jumia.com.ng/catalog/product1234568"   # Another example
            ]
        }
        
        with open('config/products.json', 'w') as f:
            json.dump(default_products, f, indent=4)
        logger.info("Created default products.json")
    
    if not os.path.exists('config/settings.json'):
        default_settings = {
            "headless": True,
            "implicit_wait": 10,
            "explicit_wait": 30,
            "output_formats": ["csv", "json", "excel"],
            "google_sheets": {
                "enabled": False,
                "credentials_file": "credentials.json",
                "spreadsheet_id": ""
            }
        }
        
        with open('config/settings.json', 'w') as f:
            json.dump(default_settings, f, indent=4)
        logger.info("Created default settings.json")
    
    # Create a .gitignore file
    if not os.path.exists('.gitignore'):
        gitignore_content = """# Data files
/data/
/historical_data.csv

# Logs
/logs/

# Credentials
/credentials.json
/config/credentials.json

# Python
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
env/
venv/
ENV/
env.bak/
venv.bak/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db
"""
        with open('.gitignore', 'w') as f:
            f.write(gitignore_content)
        logger.info("Created .gitignore file")
    
    logger.info("Project setup completed successfully!")
    print("""
    E-commerce Price Tracker Setup Complete!
    
    Next steps:
    1. Edit config/products.json to add your product URLs
    2. Configure settings in config/settings.json if needed
    3. Install requirements: pip install -r requirements.txt
    4. Run the scraper: python main.py --all
    
    For Google Sheets integration:
    1. Create a Google Cloud Platform project
    2. Enable the Google Sheets API
    3. Create service account credentials
    4. Download the JSON credentials file
    5. Place it in the project root as credentials.json
    6. Update the spreadsheet ID in config/settings.json
    """)

if __name__ == "__main__":
    setup_project()