import pandas as pd
import json
import os
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import logging

class DataExporter:
    def __init__(self):
        self.setup_logging()
        self.setup_directories()
        
    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('logs/exporter.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def setup_directories(self):
        os.makedirs('data/csv', exist_ok=True)
        os.makedirs('data/json', exist_ok=True)
        os.makedirs('data/excel', exist_ok=True)
        os.makedirs('data/charts', exist_ok=True)
        os.makedirs('logs', exist_ok=True)
    
    def export_data(self, data, formats=None):
        if formats is None:
            formats = ['csv', 'json', 'excel']
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if 'csv' in formats:
            self.export_to_csv(data, timestamp)
        
        if 'json' in formats:
            self.export_to_json(data, timestamp)
            
        if 'excel' in formats:
            self.export_to_excel(data, timestamp)
            
        # Update Google Sheets if enabled
        self.update_google_sheets(data)
        
        # Update historical data
        self.update_historical_data(data)
    
    def export_to_csv(self, data, timestamp):
        try:
            df = pd.DataFrame(data)
            filename = f"data/csv/products_{timestamp}.csv"
            df.to_csv(filename, index=False)
            self.logger.info(f"Exported data to CSV: {filename}")
            
            # Also update the latest file
            df.to_csv("data/csv/products_latest.csv", index=False)
        except Exception as e:
            self.logger.error(f"Error exporting to CSV: {str(e)}")
    
    def export_to_json(self, data, timestamp):
        try:
            filename = f"data/json/products_{timestamp}.json"
            with open(filename, 'w') as f:
                json.dump(data, f, indent=4)
            self.logger.info(f"Exported data to JSON: {filename}")
            
            # Also update the latest file
            with open("data/json/products_latest.json", 'w') as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            self.logger.error(f"Error exporting to JSON: {str(e)}")
    
    def export_to_excel(self, data, timestamp):
        try:
            df = pd.DataFrame(data)
            filename = f"data/excel/products_{timestamp}.xlsx"
            df.to_excel(filename, index=False)
            self.logger.info(f"Exported data to Excel: {filename}")
            
            # Also update the latest file
            df.to_excel("data/excel/products_latest.xlsx", index=False)
        except Exception as e:
            self.logger.error(f"Error exporting to Excel: {str(e)}")
    
    def update_google_sheets(self, data):
        try:
            # Check if Google Sheets integration is enabled
            with open('config/settings.json', 'r') as f:
                settings = json.load(f)
                
            if not settings.get('google_sheets', {}).get('enabled', False):
                return
                
            # Authenticate with Google Sheets API
            scope = ["https://spreadsheets.google.com/feeds", 
                    "https://www.googleapis.com/auth/drive"]
            
            creds_file = settings['google_sheets'].get('credentials_file', 'credentials.json')
            if not os.path.exists(creds_file):
                self.logger.warning("Google Sheets credentials file not found")
                return
                
            creds = ServiceAccountCredentials.from_json_keyfile_name(creds_file, scope)
            client = gspread.authorize(creds)
            
            # Open the spreadsheet
            spreadsheet_id = settings['google_sheets'].get('spreadsheet_id')
            if not spreadsheet_id:
                self.logger.warning("Google Sheets spreadsheet ID not configured")
                return
                
            sheet = client.open_by_key(spreadsheet_id).sheet1
            
            # Prepare data for insertion
            df = pd.DataFrame(data)
            df['scraped_at'] = pd.to_datetime(df['scraped_at'])
            
            # Clear existing data (except header)
            if sheet.row_count > 1:
                sheet.delete_rows(2, sheet.row_count)
            
            # Add new data
            records = df.to_dict('records')
            for record in records:
                row = [
                    record.get('platform', ''),
                    record.get('title', ''),
                    record.get('price', ''),
                    record.get('discount', ''),
                    record.get('rating', ''),
                    record.get('reviews', ''),
                    record.get('url', ''),
                    record.get('scraped_at', '').strftime('%Y-%m-%d %H:%M:%S') if hasattr(record.get('scraped_at', ''), 'strftime') else str(record.get('scraped_at', ''))
                ]
                sheet.append_row(row)
                
            self.logger.info("Updated Google Sheets with new data")
            
        except Exception as e:
            self.logger.error(f"Error updating Google Sheets: {str(e)}")
    
    def update_historical_data(self, data):
        try:
            historical_file = "data/historical_data.csv"
            
            # Load existing historical data if it exists
            if os.path.exists(historical_file):
                historical_df = pd.read_csv(historical_file)
            else:
                historical_df = pd.DataFrame()
            
            # Convert new data to DataFrame
            new_df = pd.DataFrame(data)
            new_df['scraped_at'] = pd.to_datetime(new_df['scraped_at'])
            
            # Append new data to historical data
            if historical_df.empty:
                historical_df = new_df
            else:
                historical_df = pd.concat([historical_df, new_df], ignore_index=True)
            
            # Save updated historical data
            historical_df.to_csv(historical_file, index=False)
            self.logger.info(f"Updated historical data with {len(new_df)} new records")
            
        except Exception as e:
            self.logger.error(f"Error updating historical data: {str(e)}")

if __name__ == "__main__":
    # Test the exporter
    exporter = DataExporter()
    sample_data = [
        {
            'platform': 'test',
            'title': 'Test Product',
            'price': '$99.99',
            'discount': '10%',
            'rating': '4.5',
            'reviews': '100',
            'url': 'http://example.com',
            'scraped_at': datetime.now().isoformat()
        }
    ]
    exporter.export_data(sample_data)