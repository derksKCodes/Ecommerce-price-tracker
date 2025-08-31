import schedule
import time
import subprocess
import logging
from datetime import datetime
import os

class TaskScheduler:
    def __init__(self):
        self.setup_logging()
        
    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('logs/scheduler.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def run_scraper(self):
        self.logger.info("Starting scheduled scraping task...")
        try:
            # Run the scraper
            from scraper import EcommerceScraper
            from exporter import DataExporter
            from visualizer import DataVisualizer
            
            scraper = EcommerceScraper(headless=True)
            data = scraper.scrape_all_products()
            
            if data:
                exporter = DataExporter()
                exporter.export_data(data)
                
                visualizer = DataVisualizer()
                visualizer.generate_price_trends()
                visualizer.generate_comparison_charts()
                
                self.logger.info(f"Successfully completed scraping {len(data)} products")
            else:
                self.logger.warning("No data was scraped")
                
        except Exception as e:
            self.logger.error(f"Error in scheduled task: {str(e)}")
    
    def schedule_daily_task(self, time_str="09:00"):
        """Schedule the scraping task to run daily at the specified time"""
        schedule.every().day.at(time_str).do(self.run_scraper)
        
        self.logger.info(f"Scheduled daily task at {time_str}")
        
        # Run immediately on first start
        self.run_scraper()
        
        # Keep the scheduler running
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    
    def schedule_hourly_task(self):
        """Schedule the scraping task to run hourly"""
        schedule.every().hour.do(self.run_scraper)
        
        self.logger.info("Scheduled hourly task")
        
        # Run immediately on first start
        self.run_scraper()
        
        # Keep the scheduler running
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute

if __name__ == "__main__":
    scheduler = TaskScheduler()
    
    # Run daily at 9 AM
    # scheduler.schedule_daily_task("09:00")
    
    # Alternatively, run hourly
    scheduler.schedule_hourly_task()