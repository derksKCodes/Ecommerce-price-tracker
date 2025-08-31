#!/usr/bin/env python3
"""
E-commerce Price Tracker - Main Script
"""
import argparse
from src.scraper import EcommerceScraper
from src.exporter import DataExporter
from src.visualizer import DataVisualizer
from src.scheduler import TaskScheduler
from src.utils import setup_logging

def main():
    parser = argparse.ArgumentParser(description="E-commerce Price Tracker")
    parser.add_argument('--scrape', action='store_true', help='Run scraping once')
    parser.add_argument('--export', action='store_true', help='Export existing data')
    parser.add_argument('--visualize', action='store_true', help='Generate visualizations')
    parser.add_argument('--schedule', action='store_true', help='Start scheduled tasks')
    parser.add_argument('--headless', action='store_true', default=True, help='Run browser in headless mode')
    parser.add_argument('--all', action='store_true', help='Run all steps: scrape, export, visualize')
    
    args = parser.parse_args()
    logger = setup_logging('main')
    
    if args.all or args.scrape:
        logger.info("Starting scraping process...")
        scraper = EcommerceScraper(headless=args.headless)
        data = scraper.scrape_all_products()
        
        if data:
            logger.info(f"Successfully scraped {len(data)} products")
            
            if args.all or args.export:
                logger.info("Exporting data...")
                exporter = DataExporter()
                exporter.export_data(data)
            
            if args.all or args.visualize:
                logger.info("Generating visualizations...")
                visualizer = DataVisualizer()
                visualizer.generate_price_trends()
                visualizer.generate_comparison_charts()
                visualizer.generate_dashboard()
        else:
            logger.warning("No data was scraped")
    
    elif args.export:
        logger.info("Exporting existing data...")
        # This would need to be implemented to load existing data
        logger.warning("Export-only mode requires existing data structure")
    
    elif args.visualize:
        logger.info("Generating visualizations from historical data...")
        visualizer = DataVisualizer()
        visualizer.generate_price_trends()
        visualizer.generate_comparison_charts()
        visualizer.generate_dashboard()
    
    elif args.schedule:
        logger.info("Starting scheduled task runner...")
        scheduler = TaskScheduler()
        scheduler.schedule_daily_task()
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()