# E-commerce Price Tracker

A Python-based web scraper that tracks product prices, ratings, reviews, and discounts from Amazon, eBay, AliExpress, and Jumia.

## Features

- Scrape product data from multiple e-commerce platforms
- Store data in CSV, JSON, Excel, and Google Sheets
- Generate price trend visualizations and charts
- Schedule automatic daily or hourly runs
- Handle multiple product URLs from a config file
- Maintain price history for each product
- Logging for all major operations

## Project Structure

```
.gitignore
main.py
README.md
requirements.txt
setup_script.py
config/
    products.json
    selectors.json
    settings.json
data/
    historical_data.csv
    charts/
        dashboard.png
        platform_comparison.png
        rating_distribution.png
    csv/
        products_*.csv
    excel/
        products_*.xlsx
    json/
        products_*.json
logs/
    exporter.log
    main.log
    scraper.log
    visualizer.log
src/
    .env
    exporter.py
    scheduler.py
    scraper.py
    utils.py
    visualizer.py
```

## Installation

1. **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd ecommerce-price-tracker
    ```

2. **Run the setup script to create folders and default config files:**
    ```bash
    python setup_script.py
    ```

3. **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4. **Configure your products:**
    - Edit [config/products.json](config/products.json) to add your product URLs.

5. **Configure settings:**
    - Edit [config/settings.json](config/settings.json) to adjust scraping and export options.

6. **(Optional) Set up Google Sheets integration:**
    - Create a Google Cloud Platform project
    - Enable the Google Sheets API
    - Create service account credentials and download the JSON file
    - Place the credentials file in the project root as `credentials.json`
    - Update the spreadsheet ID in [config/settings.json](config/settings.json)

## Usage

Run the main script with desired options:

```bash
# Run complete process (scrape, export, visualize)
python main.py --all

# Run only scraping
python main.py --scrape

# Export existing data
python main.py --export

# Generate visualizations from historical data
python main.py --visualize

# Start scheduled daily tasks (default: daily at 09:00)
python main.py --schedule

# Show help
python main.py --help
```

## Configuration

### Product Configuration

Edit [config/products.json](config/products.json):

```json
{
  "amazon": [
    "https://www.amazon.com/dp/PRODUCT_ID"
  ],
  "ebay": [
    "https://www.ebay.com/itm/ITEM_ID"
  ],
  "aliexpress": [
    "https://www.aliexpress.com/item/PRODUCT_ID.html"
  ],
  "jumia": [
    "https://www.jumia.com.ng/catalog/product/PRODUCT_ID"
  ]
}
```

### Settings Configuration

Edit [config/settings.json](config/settings.json):

```json
{
  "headless": true,
  "implicit_wait": 10,
  "explicit_wait": 30,
  "output_formats": ["csv", "json", "excel"],
  "google_sheets": {
    "enabled": false,
    "credentials_file": "credentials.json",
    "spreadsheet_id": ""
  }
}
```

## Output Files

- CSV: [data/csv/products_*.csv](data/csv/)
- JSON: [data/json/products_*.json](data/json/)
- Excel: [data/excel/products_*.xlsx](data/excel/)
- Charts: [data/charts/](data/charts/)
- Historical data: [data/historical_data.csv](data/historical_data.csv)
- Logs: [logs/](logs/)

## Scheduling

- Built-in scheduler: `python main.py --schedule`
- Or use cron/Task Scheduler for automation.

## Troubleshooting

- **WebDriver issues:** Chrome must be installed; ChromeDriver is auto-managed.
- **Scraping failures:** Some sites may block bots; increase wait times in settings.
- **Google Sheets:** Ensure credentials and spreadsheet sharing are correct.
- **Memory issues:** For large product lists, increase system memory.

## Legal Considerations

- Respect robots.txt files and site terms.
- Add delays between requests.
- Use scraped data responsibly.

## Contributing

- Fork the repository
- Create a feature branch
- Make your changes
- Add tests if applicable
- Submit a pull request

## License

MIT License - see the LICENSE file for details.