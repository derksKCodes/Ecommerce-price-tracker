import json
import logging
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from urllib.parse import urlparse
import re
from pathlib import Path
class EcommerceScraper:
    def __init__(self, headless=True):
        self.setup_logging()
        self.driver = self.setup_driver(headless)
        self.data = []
        
    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('logs/scraper.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def setup_driver(self, headless):
        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)

        # ✅ Ensure we pick the .exe file, not a .txt
        driver_path = ChromeDriverManager().install()
        driver_path = str(Path(driver_path).with_name("chromedriver.exe"))

        self.logger.info(f"Using ChromeDriver executable: {driver_path}")

        service = Service(driver_path)
        driver = webdriver.Chrome(service=service, options=chrome_options)

        return driver
        
  

    
    def load_product_urls(self, config_file='config/products.json'):
        try:
            with open(config_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            self.logger.error(f"Config file {config_file} not found")
            return {}
        except json.JSONDecodeError:
            self.logger.error(f"Invalid JSON in {config_file}")
            return {}
    
    def scrape_all_products(self):
        product_urls = self.load_product_urls()
        for platform, urls in product_urls.items():
            for url in urls:
                try:
                    self.logger.info(f"Scraping {url}")
                    product_data = self.scrape_product(url, platform)
                    if product_data:
                        product_data['scraped_at'] = datetime.now().isoformat()
                        self.data.append(product_data)
                        self.logger.info(f"Successfully scraped: {product_data['title'][:50]}...")
                    else:
                        self.logger.warning(f"Failed to scrape product data from {url}")
                except Exception as e:
                    self.logger.error(f"Error scraping {url}: {str(e)}")
        
        self.driver.quit()
        return self.data
    
    def scrape_product(self, url, platform):
        self.driver.get(url)
        time.sleep(3)  # Initial page load
        
        try:
            if platform == 'amazon':
                return self.scrape_amazon()
            elif platform == 'ebay':
                return self.scrape_ebay()
            elif platform == 'aliexpress':
                return self.scrape_aliexpress()
            elif platform == 'jumia':
                return self.scrape_jumia()
            else:
                self.logger.warning(f"Unsupported platform: {platform}")
                return None
        except Exception as e:
            self.logger.error(f"Error scraping {platform} product: {str(e)}")
            return None
    
    def scrape_amazon(self):
        product_data = {
            'platform': 'amazon',
            'url': self.driver.current_url
        }
        
        try:
            # Title
            try:
                title_elem = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.ID, "productTitle"))
                )
                product_data['title'] = title_elem.text.strip()
            except TimeoutException:
                try:
                    title_elem = self.driver.find_element(By.CSS_SELECTOR, "h1.a-size-large")
                    product_data['title'] = title_elem.text.strip()
                except NoSuchElementException:
                    product_data['title'] = "Not Found"
            
            # Price
            try:
                price_whole = self.driver.find_element(By.CSS_SELECTOR, "span.a-price-whole")
                price_fraction = self.driver.find_element(By.CSS_SELECTOR, "span.a-price-fraction")
                product_data['price'] = f"{price_whole.text}.{price_fraction.text}"
            except NoSuchElementException:
                try:
                    price_elem = self.driver.find_element(By.CSS_SELECTOR, "span.a-price[data-a-size='xl']")
                    product_data['price'] = price_elem.text.strip().replace('\n', '.')
                except NoSuchElementException:
                    try:
                        price_elem = self.driver.find_element(By.ID, "priceblock_ourprice")
                        product_data['price'] = price_elem.text.strip()
                    except NoSuchElementException:
                        product_data['price'] = "Not Found"
            
            # Discount
            try:
                discount_elem = self.driver.find_element(By.CSS_SELECTOR, "span.savingsPercentage")
                product_data['discount'] = discount_elem.text.strip()
            except NoSuchElementException:
                product_data['discount'] = "0%"
            
            # Rating
            try:
                rating_elem = self.driver.find_element(By.CSS_SELECTOR, "span.a-icon-alt")
                rating_text = rating_elem.get_attribute("innerHTML")
                product_data['rating'] = rating_text.split(" ")[0]
            except NoSuchElementException:
                product_data['rating'] = "Not Found"
            
            # Reviews count
            try:
                reviews_elem = self.driver.find_element(By.ID, "acrCustomerReviewText")
                product_data['reviews'] = reviews_elem.text.split(" ")[0]
            except NoSuchElementException:
                product_data['reviews'] = "0"
                
        except Exception as e:
            self.logger.error(f"Error parsing Amazon product: {str(e)}")
            return None
            
        return product_data
    
    def scrape_ebay(self):
        product_data = {
            'platform': 'ebay',
            'url': self.driver.current_url
        }
        
        try:
            # Title
            try:
                title_elem = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "h1.x-item-title__mainTitle"))
                )
                product_data['title'] = title_elem.text.strip()
            except TimeoutException:
                try:
                    title_elem = self.driver.find_element(By.CSS_SELECTOR, "h1#itemTitle")
                    product_data['title'] = title_elem.text.replace("Details about", "").strip()
                except NoSuchElementException:
                    product_data['title'] = "Not Found"
            
            # Price
            try:
                price_elem = self.driver.find_element(By.CSS_SELECTOR, "div.x-price-primary")
                product_data['price'] = price_elem.text.strip()
            except NoSuchElementException:
                try:
                    price_elem = self.driver.find_element(By.CSS_SELECTOR, "span#prcIsum")
                    product_data['price'] = price_elem.text.strip()
                except NoSuchElementException:
                    product_data['price'] = "Not Found"
            
            # Discount - eBay typically doesn't show discounts like other platforms
            product_data['discount'] = "0%"
            
            # Rating
            try:
                rating_elem = self.driver.find_element(By.CSS_SELECTOR, "div.x-seller-rating")
                rating_text = rating_elem.text.strip()
                product_data['rating'] = rating_text.split(" ")[0]
            except NoSuchElementException:
                product_data['rating'] = "Not Found"
            
            # Reviews count
            try:
                reviews_elem = self.driver.find_element(By.CSS_SELECTOR, "span#si-fb")
                product_data['reviews'] = reviews_elem.text.split(" ")[0]
            except NoSuchElementException:
                product_data['reviews'] = "0"
                
        except Exception as e:
            self.logger.error(f"Error parsing eBay product: {str(e)}")
            return None
            
        return product_data
    
    def scrape_aliexpress(self):
        product_data = {
            'platform': 'aliexpress',
            'url': self.driver.current_url
        }
        
        try:
            # Title
            try:
                title_elem = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "h1.product-title-text"))
                )
                product_data['title'] = title_elem.text.strip()
            except TimeoutException:
                product_data['title'] = "Not Found"
            
            # Price
            try:
                price_elem = self.driver.find_element(By.CSS_SELECTOR, "div.product-price-current")
                product_data['price'] = price_elem.text.strip()
            except NoSuchElementException:
                try:
                    price_elem = self.driver.find_element(By.CSS_SELECTOR, "span.price")
                    product_data['price'] = price_elem.text.strip()
                except NoSuchElementException:
                    product_data['price'] = "Not Found"
            
            # Discount
            try:
                discount_elem = self.driver.find_element(By.CSS_SELECTOR, "span.price-discount-percentage")
                product_data['discount'] = discount_elem.text.strip()
            except NoSuchElementException:
                product_data['discount'] = "0%"
            
            # Rating
            try:
                rating_elem = self.driver.find_element(By.CSS_SELECTOR, "span.overview-rating-average")
                product_data['rating'] = rating_elem.text.strip()
            except NoSuchElementException:
                product_data['rating'] = "Not Found"
            
            # Reviews count
            try:
                reviews_elem = self.driver.find_element(By.CSS_SELECTOR, "span.product-reviewer-reviews")
                reviews_text = reviews_elem.text.strip()
                product_data['reviews'] = reviews_text.split(" ")[0]
            except NoSuchElementException:
                product_data['reviews'] = "0"
                
        except Exception as e:
            self.logger.error(f"Error parsing AliExpress product: {str(e)}")
            return None
            
        return product_data
    
    def scrape_jumia(self):
        product_data = {
            'platform': 'jumia',
            'url': self.driver.current_url
        }
        
        try:
            # Title
            try:
                title_elem = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "h1.-fs20.-pts.-pbxs"))
                )
                product_data['title'] = title_elem.text.strip()
            except TimeoutException:
                product_data['title'] = "Not Found"
            
            # Price
            try:
                price_elem = self.driver.find_element(By.CSS_SELECTOR, "span.-b.-ltr.-tal.-fs24")
                product_data['price'] = price_elem.text.strip()
            except NoSuchElementException:
                try:
                    price_elem = self.driver.find_element(By.CSS_SELECTOR, "span.-b.-ltr.-tal.-fs24")
                    product_data['price'] = price_elem.text.strip()
                except NoSuchElementException:
                    product_data['price'] = "Not Found"
            
            # Discount
            try:
                discount_elem = self.driver.find_element(By.CSS_SELECTOR, "span.bdg._dsct._dyn.-mls")
                product_data['discount'] = discount_elem.text.strip()
            except NoSuchElementException:
                product_data['discount'] = "0%"
            
            # Rating
            try:
                rating_elem = self.driver.find_element(By.CSS_SELECTOR, "div.stars._m._al")
                rating_text = rating_elem.get_attribute("style")
                # Extract width percentage which represents rating
                width_match = re.search(r'width:\s*(\d+)%', rating_text)
                if width_match:
                    rating_percent = int(width_match.group(1))
                    product_data['rating'] = str(rating_percent / 20)  # Convert to 5-star scale
                else:
                    product_data['rating'] = "Not Found"
            except NoSuchElementException:
                product_data['rating'] = "Not Found"
            
            # Reviews count
            try:
                reviews_elem = self.driver.find_element(By.CSS_SELECTOR, "a.-plxs._more")
                reviews_text = reviews_elem.text.strip()
                product_data['reviews'] = reviews_text.split(" ")[0]
            except NoSuchElementException:
                product_data['reviews'] = "0"
                
        except Exception as e:
            self.logger.error(f"Error parsing Jumia product: {str(e)}")
            return None
            
        return product_data

if __name__ == "__main__":
    scraper = EcommerceScraper(headless=True)
    data = scraper.scrape_all_products()
    print(f"Scraped {len(data)} products")