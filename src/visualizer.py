import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
from datetime import datetime
import logging
import json
import re
class DataVisualizer:
    def __init__(self):
        self.setup_logging()
        self.setup_directories()
        self.setup_style()
        
    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('logs/visualizer.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def setup_directories(self):
        os.makedirs('data/charts', exist_ok=True)
        
    def setup_style(self):
        plt.style.use('default')
        sns.set_palette("husl")
        
    def load_historical_data(self):
        try:
            historical_file = "data/historical_data.csv"
            if not os.path.exists(historical_file):
                self.logger.warning("Historical data file not found")
                return pd.DataFrame()
                
            df = pd.read_csv(historical_file)
            df['scraped_at'] = pd.to_datetime(df['scraped_at'])
            
            # Clean price data
            df['price_numeric'] = df['price'].apply(self.extract_numeric_price)
            
            return df
        except Exception as e:
            self.logger.error(f"Error loading historical data: {str(e)}")
            return pd.DataFrame()
    
    def extract_numeric_price(self, price_str):
        if pd.isna(price_str) or price_str == "Not Found":
            return None
            
        try:
            # Remove currency symbols and commas
            cleaned = re.sub(r'[^\d.]', '', str(price_str))
            return float(cleaned)
        except:
            return None
    
    def generate_price_trends(self):
        df = self.load_historical_data()
        if df.empty:
            self.logger.warning("No historical data available for generating trends")
            return
            
        # Get unique products
        products = df['title'].unique()
        
        for product in products:
            if pd.isna(product) or product == "Not Found":
                continue
                
            product_data = df[df['title'] == product]
            
            # Skip if not enough data points
            if len(product_data) < 2:
                continue
                
            plt.figure(figsize=(10, 6))
            
            # Plot price trend
            plt.plot(product_data['scraped_at'], product_data['price_numeric'], 
                    marker='o', linewidth=2, markersize=6)
            
            plt.title(f"Price Trend for {product[:50]}...")
            plt.xlabel("Date")
            plt.ylabel("Price")
            plt.xticks(rotation=45)
            plt.tight_layout()
            
            # Save the chart
            safe_product_name = "".join(c for c in product if c.isalnum() or c in (' ',)).rstrip()
            safe_product_name = safe_product_name[:50]  # Limit filename length
            filename = f"data/charts/price_trend_{safe_product_name}.png"
            plt.savefig(filename)
            plt.close()
            
            self.logger.info(f"Generated price trend chart for: {product[:30]}...")
    
    def generate_comparison_charts(self):
        df = self.load_historical_data()
        if df.empty:
            return
            
        # Get latest data for each product
        latest_data = df.loc[df.groupby('title')['scraped_at'].idxmax()]
        
        # Platform comparison
        plt.figure(figsize=(12, 8))
        platform_avg = latest_data.groupby('platform')['price_numeric'].mean().dropna()
        if platform_avg.empty:
            logging.warning("No data available for comparison charts. Skipping visualization.")
            return
        platform_avg.plot(kind='bar')
        plt.title("Average Price by Platform")
        plt.xlabel("Platform")
        plt.ylabel("Average Price")
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig("data/charts/platform_comparison.png")
        plt.close()
        
        # Rating distribution
        plt.figure(figsize=(10, 6))
        ratings = pd.to_numeric(latest_data['rating'], errors='coerce').dropna()
        if not ratings.empty:
            plt.hist(ratings, bins=10, edgecolor='black')
            plt.title("Rating Distribution")
            plt.xlabel("Rating")
            plt.ylabel("Count")
            plt.tight_layout()
            plt.savefig("data/charts/rating_distribution.png")
            plt.close()
        
        self.logger.info("Generated comparison charts")
    
    def generate_dashboard(self):
        df = self.load_historical_data()
        if df.empty:
            return
            
        # Create a comprehensive dashboard
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        
        # Price trends by platform
        for i, platform in enumerate(df['platform'].unique()):
            platform_data = df[df['platform'] == platform]
            if platform_data.empty:
                continue
                
            # Get average price over time
            avg_prices = platform_data.groupby('scraped_at')['price_numeric'].mean()
            axes[0, 0].plot(avg_prices.index, avg_prices.values, label=platform, marker='o')
        
        axes[0, 0].set_title("Price Trends by Platform")
        axes[0, 0].set_xlabel("Date")
        axes[0, 0].set_ylabel("Average Price")
        axes[0, 0].legend()
        axes[0, 0].tick_params(axis='x', rotation=45)
        
        # Platform distribution
        platform_counts = df['platform'].value_counts()
        axes[0, 1].pie(platform_counts.values, labels=platform_counts.index, autopct='%1.1f%%')
        axes[0, 1].set_title("Products by Platform")
        
        # Rating vs Reviews scatter plot
        ratings = pd.to_numeric(df['rating'], errors='coerce')
        reviews = pd.to_numeric(df['reviews'], errors='coerce')
        axes[1, 0].scatter(ratings, reviews, alpha=0.6)
        axes[1, 0].set_title("Rating vs Number of Reviews")
        axes[1, 0].set_xlabel("Rating")
        axes[1, 0].set_ylabel("Reviews")
        
        # Discount distribution
        discounts = df['discount'].apply(lambda x: float(x.strip('%')) if '%' in str(x) else 0)
        axes[1, 1].hist(discounts, bins=20, edgecolor='black')
        axes[1, 1].set_title("Discount Distribution")
        axes[1, 1].set_xlabel("Discount (%)")
        axes[1, 0].set_ylabel("Count")
        
        plt.tight_layout()
        plt.savefig("data/charts/dashboard.png")
        plt.close()
        
        self.logger.info("Generated comprehensive dashboard")

if __name__ == "__main__":
    visualizer = DataVisualizer()
    visualizer.generate_price_trends()
    visualizer.generate_comparison_charts()
    visualizer.generate_dashboard()