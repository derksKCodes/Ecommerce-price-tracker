# E-commerce Price Tracker

A Python-based web scraper that automatically tracks product prices, ratings, reviews, and discounts from Amazon, eBay, AliExpress, and Jumia.

## Features

- Scrape product data from multiple e-commerce platforms
- Store data in CSV, JSON, Excel, and Google Sheets
- Generate price trend visualizations and charts
- Schedule automatic daily runs
- Handle multiple product URLs from a config file
- Maintain price history for each product

## Supported Platforms

- Amazon
- eBay
- AliExpress
- Jumia

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd ecommerce-price-tracker
Install dependencies:

bash
pip install -r requirements.txt
Download the appropriate WebDriver for your browser:

ChromeDriver will be automatically downloaded by webdriver-manager

Configure your products:

Edit config/products.json to add your product URLs

Configure settings in config/settings.json

(Optional) Set up Google Sheets integration:

Create a Google Cloud Platform project

Enable the Google Sheets API

Create service account credentials and download the JSON file

Place the credentials file in the project root as credentials.json

Update the spreadsheet ID in config/settings.json

Usage
Run the main script with desired options:

bash
# Run complete process (scrape, export, visualize)
python main.py --all

# Run only scraping
python main.py --scrape

# Generate visualizations from existing data
python main.py --visualize

# Start scheduled daily tasks
python main.py --schedule

# Show help
python main.py --help
Configuration
Product Configuration
Edit config/products.json to add product URLs:

json
{
  "amazon": [
    "https://www.amazon.com/dp/PRODUCT_ID",
    "https://www.amazon.com/dp/ANOTHER_PRODUCT_ID"
  ],
  "ebay": [
    "https://www.ebay.com/itm/ITEM_ID",
    "https://www.ebay.com/itm/ANOTHER_ITEM_ID"
  ],
  "aliexpress": [
    "https://www.aliexpress.com/item/PRODUCT_ID.html"
  ],
  "jumia": [
    "https://www.jumia.com.ng/catalog/product/PRODUCT_ID"
  ]
}
Settings Configuration
Edit config/settings.json to configure application behavior:

json
{
  "headless": true,
  "implicit_wait": 10,
  "explicit_wait": 30,
  "output_formats": ["csv", "json", "excel"],
  "google_sheets": {
    "enabled": false,
    "credentials_file": "credentials.json",
    "spreadsheet_id": "your-spreadsheet-id-here"
  }
}
Output Files
CSV files: data/csv/products_*.csv

JSON files: data/json/products_*.json

Excel files: data/excel/products_*.xlsx

Charts: data/charts/*.png

Historical data: data/historical_data.csv

Logs: logs/*.log

Scheduling
The application can be scheduled to run automatically:

Using the built-in scheduler:

bash
python main.py --schedule
Using cron (Linux/Mac) or Task Scheduler (Windows):

bash
# Run daily at 9 AM
0 9 * * * cd /path/to/ecommerce-price-tracker && python main.py --all

# Run hourly
0 * * * * cd /path/to/ecommerce-price-tracker && python main.py --all
Troubleshooting
WebDriver issues: Make sure you have Chrome installed and updated

Scraping failures: Some sites may have anti-bot measures. Try increasing wait times in settings

Google Sheets integration: Verify your credentials and spreadsheet sharing settings

Memory issues: For large numbers of products, consider increasing system memory

Legal Considerations
Respect robots.txt files

Add delays between requests to avoid overloading servers

Check terms of service for each platform

Use scraped data responsibly and for personal use only

Contributing
Fork the repository

Create a feature branch

Make your changes

Add tests if applicable

Submit a pull request

License
This project is licensed under the MIT License - see the LICENSE file for details.

text


How to Use This Project
Run the setup script to create the project structure:

bash
python setup.py
Install the required dependencies:

bash
pip install -r requirements.txt
Edit the config/products.json file to add your product URLs

Run the scraper:

bash
python main.py --all
For scheduled runs, either:

Use the built-in scheduler: python main.py --schedule

Set up a cron job or Task Scheduler to run python main.py --all daily

This complete implementation provides a robust e-commerce price tracking system that can scrape data from multiple platforms, store it in various formats, generate visualizations, and run on a schedule. The code includes error handling, logging, and configuration options to make it production-ready.