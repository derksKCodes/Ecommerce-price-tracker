import json
import logging
import time
import re
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
from webdriver_manager.chrome import ChromeDriverManager


class EcommerceScraper:
    def __init__(self, headless=True):
        self.setup_logging()
        self.driver = self.setup_driver(headless)
        self.data = []

    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
            handlers=[
                logging.FileHandler("logs/scraper.log"),
                logging.StreamHandler(),
            ],
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
        chrome_options.add_experimental_option("useAutomationExtension", False)

        driver_path = ChromeDriverManager().install()
        driver_path = str(Path(driver_path).with_name("chromedriver.exe"))
        self.logger.info(f"Using ChromeDriver executable: {driver_path}")

        service = Service(driver_path)
        driver = webdriver.Chrome(service=service, options=chrome_options)
        return driver

    def load_product_urls(self, config_file="config/products.json"):
        try:
            with open(config_file, "r") as f:
                return json.load(f)
        except FileNotFoundError:
            self.logger.error(f"Config file {config_file} not found")
            return {}
        except json.JSONDecodeError:
            self.logger.error(f"Invalid JSON in {config_file}")
            return {}

    def detect_page_type(self, url, platform):
        if platform == "amazon":
            return "product" if "/dp/" in url or "/gp/" in url or "/product/" in url else "search"
        if platform == "ebay":
            return "product" if "/itm/" in url else "search"
        if platform == "aliexpress":
            return "product" if "/item/" in url else "search"
        if platform == "jumia":
            return "product" if "/catalog/" in url or "/product/" in url else "search"
        return "product"

    def scrape_all_products(self):
        product_urls = self.load_product_urls()
        for platform, urls in product_urls.items():
            for url in urls:
                try:
                    self.logger.info(f"Scraping {url}")
                    product_data = self.scrape_product(url, platform)

                    if product_data:
                        if isinstance(product_data, list):  # search results
                            for item in product_data:
                                item["scraped_at"] = datetime.now().isoformat()
                                self.data.append(item)
                        else:  # single product
                            product_data["scraped_at"] = datetime.now().isoformat()
                            self.data.append(product_data)

                        self.logger.info(f"Successfully scraped: {len(product_data) if isinstance(product_data, list) else 1} items from {url}")
                    else:
                        self.logger.warning(f"Failed to scrape data from {url}")
                except Exception as e:
                    self.logger.error(f"Error scraping {url}: {str(e)}")
                    import traceback
                    self.logger.error(traceback.format_exc())

        self.driver.quit()
        return self.data

    def scrape_product(self, url, platform):
        try:
            self.driver.get(url)
            # Wait for page to load
            time.sleep(5)
            
            # Check if we got a CAPTCHA or access denied
            if "captcha" in self.driver.page_source.lower() or "access denied" in self.driver.page_source.lower():
                self.logger.warning(f"CAPTCHA or access denied detected on {url}")
                return None

            page_type = self.detect_page_type(url, platform)

            if platform == "amazon":
                return self.scrape_amazon() if page_type == "product" else self.scrape_amazon_search()
            elif platform == "ebay":
                return self.scrape_ebay() if page_type == "product" else self.scrape_ebay_search()
            elif platform == "aliexpress":
                return self.scrape_aliexpress() if page_type == "product" else self.scrape_aliexpress_search()
            elif platform == "jumia":
                return self.scrape_jumia() if page_type == "product" else self.scrape_jumia_search()
            else:
                self.logger.warning(f"Unsupported platform: {platform}")
                return None
        except Exception as e:
            self.logger.error(f"Error scraping {platform}: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
            return None

    # -------------------- AMAZON --------------------
    def scrape_amazon(self):
        product_data = {"platform": "amazon", "url": self.driver.current_url}
        try:
            # Title
            try:
                title_elem = WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "a-size-base-plus"))
                )
                product_data["title"] = title_elem.text.strip()
            except (TimeoutException, NoSuchElementException):
                try:
                    title_elem = self.driver.find_element(By.CSS_SELECTOR, "h1.a-size-large")
                    product_data["title"] = title_elem.text.strip()
                except NoSuchElementException:
                    product_data["title"] = "Not Found"

            # Price
            try:
                # Try multiple price selectors
                price_selectors = [
                    "span.a-price-whole",
                    "span.a-price[data-a-size='xl']",
                    "#priceblock_ourprice",
                    "#priceblock_dealprice",
                    ".a-price .a-offscreen"
                ]
                
                price_found = False
                for selector in price_selectors:
                    try:
                        price_elem = self.driver.find_element(By.CSS_SELECTOR, selector)
                        if selector == "span.a-price-whole":
                            try:
                                price_fraction = self.driver.find_element(By.CSS_SELECTOR, "span.a-price-fraction")
                                product_data["price"] = f"{price_elem.text}.{price_fraction.text}"
                            except NoSuchElementException:
                                product_data["price"] = price_elem.text
                        else:
                            product_data["price"] = price_elem.text.strip()
                        price_found = True
                        break
                    except NoSuchElementException:
                        continue
                
                if not price_found:
                    product_data["price"] = "Not Found"
            except Exception as e:
                product_data["price"] = "Not Found"
                self.logger.warning(f"Error getting price: {e}")

            # Discount
            try:
                discount_elem = self.driver.find_element(By.CSS_SELECTOR, "span.savingsPercentage")
                product_data["discount"] = discount_elem.text.strip()
            except NoSuchElementException:
                product_data["discount"] = "0%"

            # Rating
            try:
                rating_elem = self.driver.find_element(By.CSS_SELECTOR, "span.a-icon-alt")
                rating_text = rating_elem.get_attribute("innerHTML")
                product_data["rating"] = rating_text.split(" ")[0]
            except NoSuchElementException:
                product_data["rating"] = "Not Found"

            # Reviews count
            try:
                reviews_elem = self.driver.find_element(By.ID, "acrCustomerReviewText")
                product_data["reviews"] = reviews_elem.text.split(" ")[0]
            except NoSuchElementException:
                product_data["reviews"] = "0"
                
        except Exception as e:
            self.logger.error(f"Error parsing Amazon product: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
            return None
            
        return product_data
    # Update the scrape_amazon_search method in scraper.py

    def scrape_amazon_search(self):
        results = []
        try:
            # Wait for search results to load
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "[data-component-type='s-search-result']"))
            )
        except TimeoutException:
            self.logger.warning("Amazon search results not found or took too long to load")
            return results

        try:
            items = self.driver.find_elements(
                By.CSS_SELECTOR,
                "[data-component-type='s-search-result']"
            )
            
            self.logger.info(f"Found {len(items)} search results on Amazon")
            
            for elem in items[:10]:  # limit to first 10 results
                try:
                    # Title - try multiple selectors
                    title = "Not Found"
                    title_selectors = [
                        "h2 a span",  # Main title selector
                        "span.a-text-normal",  # Alternative selector
                        "h2 a",  # Fallback
                        ".a-size-base-plus"  # Another alternative
                    ]
                    
                    for selector in title_selectors:
                        try:
                            title_elem = elem.find_element(By.CSS_SELECTOR, selector)
                            title = title_elem.text.strip()
                            if title and title != "":  # Only break if we got a valid title
                                break
                        except (NoSuchElementException, StaleElementReferenceException):
                            continue

                    # URL
                    link = self.driver.current_url  # Default to current URL
                    link_selectors = [
                        "h2 a",
                        "a.a-link-normal",
                        "a.a-text-normal"
                    ]
                    
                    for selector in link_selectors:
                        try:
                            link_elem = elem.find_element(By.CSS_SELECTOR, selector)
                            link = link_elem.get_attribute("href")
                            if link and link.startswith("http"):  # Only break if we got a valid link
                                break
                        except (NoSuchElementException, StaleElementReferenceException):
                            continue

                    # Price - try multiple selectors
                    price = "Not Found"
                    price_selectors = [
                        "span.a-price",  # Main price container
                        "span.a-price-whole",  # Whole price part
                        "span.a-offscreen",  # Screen reader price
                        ".a-price-range"  # Price range
                    ]
                    
                    for selector in price_selectors:
                        try:
                            price_elem = elem.find_element(By.CSS_SELECTOR, selector)
                            price_text = price_elem.text.strip()
                            if price_text and price_text != "":  # Only use if we got text
                                price = price_text.replace("\n", ".")
                                break
                        except (NoSuchElementException, StaleElementReferenceException):
                            continue

                    # Rating - for search results
                    rating = "Not Found"
                    rating_selectors = [
                        "span.a-icon-alt",
                        ".a-icon-star",
                        "[aria-label*='out of']"
                    ]
                    
                    for selector in rating_selectors:
                        try:
                            rating_elem = elem.find_element(By.CSS_SELECTOR, selector)
                            rating_text = rating_elem.get_attribute("innerHTML") if selector == "span.a-icon-alt" else rating_elem.text
                            if rating_text and "out of" in rating_text:
                                rating = rating_text.split(" ")[0]
                                break
                            elif rating_text:
                                # Try to extract numeric rating
                                numbers = re.findall(r'\d+\.\d+|\d+', rating_text)
                                if numbers:
                                    rating = numbers[0]
                                    break
                        except (NoSuchElementException, StaleElementReferenceException):
                            continue

                    # Reviews - for search results
                    reviews = "0"
                    reviews_selectors = [
                        "span.a-size-base",
                        ".a-size-small",
                        "[aria-label*='ratings']",
                        "[aria-label*='reviews']"
                    ]
                    
                    for selector in reviews_selectors:
                        try:
                            reviews_elem = elem.find_element(By.CSS_SELECTOR, selector)
                            reviews_text = reviews_elem.text.strip()
                            # Extract numbers from reviews text
                            numbers = re.findall(r'\d+', reviews_text)
                            if numbers:
                                reviews = numbers[0]
                                break
                            elif reviews_text.isdigit():  # If it's already a number
                                reviews = reviews_text
                                break
                        except (NoSuchElementException, StaleElementReferenceException):
                            continue

                    results.append({
                        "platform": "amazon",
                        "title": title,
                        "url": link,
                        "price": price,
                        "discount": "0%",
                        "rating": rating,
                        "reviews": reviews
                    })
                    
                except StaleElementReferenceException:
                    continue
                except Exception as e:
                    self.logger.warning(f"Error parsing search result: {e}")
                    continue
                    
        except Exception as e:
            self.logger.error(f"Error processing Amazon search results: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
            
        return results

    # -------------------- EBAY --------------------
    def scrape_ebay(self):
        product_data = {"platform": "ebay", "url": self.driver.current_url}
        try:
            # Title
            try:
                title_elem = WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "h1.x-item-title__mainTitle"))
                )
                product_data["title"] = title_elem.text.strip()
            except TimeoutException:
                try:
                    title_elem = self.driver.find_element(By.CSS_SELECTOR, "h1#itemTitle")
                    product_data["title"] = title_elem.text.replace("Details about", "").strip()
                except NoSuchElementException:
                    product_data["title"] = "Not Found"

            # Price
            try:
                price_elem = self.driver.find_element(By.CSS_SELECTOR, "div.x-price-primary")
                product_data["price"] = price_elem.text.strip()
            except NoSuchElementException:
                try:
                    price_elem = self.driver.find_element(By.CSS_SELECTOR, "span#prcIsum")
                    product_data["price"] = price_elem.text.strip()
                except NoSuchElementException:
                    product_data["price"] = "Not Found"

            product_data["discount"] = "0%"

            # Rating
            try:
                rating_elem = self.driver.find_element(By.CSS_SELECTOR, "div.x-seller-rating")
                rating_text = rating_elem.text.strip()
                product_data["rating"] = rating_text.split(" ")[0]
            except NoSuchElementException:
                product_data["rating"] = "Not Found"

            # Reviews count
            try:
                reviews_elem = self.driver.find_element(By.CSS_SELECTOR, "span#si-fb")
                product_data["reviews"] = reviews_elem.text.split(" ")[0]
            except NoSuchElementException:
                product_data["reviews"] = "0"
                
        except Exception as e:
            self.logger.error(f"Error parsing eBay product: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
            return None
            
        return product_data

    def scrape_ebay_search(self):
        results = []
        try:
            # Wait for search results
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "li.s-item"))
            )
            
            items = self.driver.find_elements(By.CSS_SELECTOR, "li.s-item")
            self.logger.info(f"Found {len(items)} search results on eBay")
            
            for elem in items[:10]:
                try:
                    # Skip the first item which is often a template
                    if "s-item__placeholder" in elem.get_attribute("class"):
                        continue
                        
                    title = elem.find_element(By.CSS_SELECTOR, "div.s-item__title span").text
                    link = elem.find_element(By.CSS_SELECTOR, "a.s-item__link").get_attribute("href")
                    
                    try:
                        price = elem.find_element(By.CSS_SELECTOR, "span.s-item__price").text
                    except NoSuchElementException:
                        price = "Not Found"
                        
                    try:
                        rating_elem = elem.find_element(By.CSS_SELECTOR, "div.x-star-rating")
                        rating = rating_elem.text.strip()
                    except NoSuchElementException:
                        rating = "Not Found"
                        
                    try:
                        reviews_elem = elem.find_element(By.CSS_SELECTOR, "span.s-item__reviews-count")
                        reviews = reviews_elem.text.strip().replace('(', '').replace(')', '')
                    except NoSuchElementException:
                        reviews = "0"
                        
                    results.append({
                        "platform": "ebay", 
                        "title": title, 
                        "url": link, 
                        "price": price, 
                        "discount": "0%", 
                        "rating": rating, 
                        "reviews": reviews
                    })
                except StaleElementReferenceException:
                    continue
                except Exception as e:
                    self.logger.warning(f"Error parsing eBay search result: {e}")
                    continue
                    
        except TimeoutException:
            self.logger.warning("eBay search results not found or took too long to load")
        except Exception as e:
            self.logger.error(f"Error processing eBay search results: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
            
        return results

    # -------------------- ALIEXPRESS --------------------
    def scrape_aliexpress(self):
        product_data = {"platform": "aliexpress", "url": self.driver.current_url}
        try:
            # Title
            try:
                title_elem = WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "h1.product-title-text"))
                )
                product_data["title"] = title_elem.text.strip()
            except TimeoutException:
                product_data["title"] = "Not Found"

            # Price
            try:
                price_elem = self.driver.find_element(By.CSS_SELECTOR, "div.product-price-current")
                product_data["price"] = price_elem.text.strip()
            except NoSuchElementException:
                try:
                    price_elem = self.driver.find_element(By.CSS_SELECTOR, "span.price")
                    product_data["price"] = price_elem.text.strip()
                except NoSuchElementException:
                    product_data["price"] = "Not Found"

            # Discount
            try:
                discount_elem = self.driver.find_element(By.CSS_SELECTOR, "span.price-discount-percentage")
                product_data["discount"] = discount_elem.text.strip()
            except NoSuchElementException:
                product_data["discount"] = "0%"

            # Rating
            try:
                rating_elem = self.driver.find_element(By.CSS_SELECTOR, "span.overview-rating-average")
                product_data["rating"] = rating_elem.text.strip()
            except NoSuchElementException:
                product_data["rating"] = "Not Found"

            # Reviews count
            try:
                reviews_elem = self.driver.find_element(By.CSS_SELECTOR, "span.product-reviewer-reviews")
                reviews_text = reviews_elem.text.strip()
                product_data["reviews"] = reviews_text.split(" ")[0]
            except NoSuchElementException:
                product_data["reviews"] = "0"
                
        except Exception as e:
            self.logger.error(f"Error parsing AliExpress product: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
            return None
            
        return product_data

    def scrape_aliexpress_search(self):
        results = []
        try:
            # Wait for search results
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-product-id]"))
            )
            
            items = self.driver.find_elements(By.CSS_SELECTOR, "div[data-product-id]")
            self.logger.info(f"Found {len(items)} search results on AliExpress")
            
            for elem in items[:10]:
                try:
                    title = elem.find_element(By.CSS_SELECTOR, "a._3t7zg._2f4Ho").text
                    link = elem.find_element(By.CSS_SELECTOR, "a._3t7zg._2f4Ho").get_attribute("href")
                    
                    try:
                        price = elem.find_element(By.CSS_SELECTOR, "span._12A8D").text
                    except NoSuchElementException:
                        price = "Not Found"
                        
                    try:
                        rating = elem.find_element(By.CSS_SELECTOR, "span.eXPaM").text
                    except NoSuchElementException:
                        rating = "Not Found"
                        
                    try:
                        reviews = elem.find_element(By.CSS_SELECTOR, "span._1kNf9").text
                    except NoSuchElementException:
                        reviews = "0"
                        
                    results.append({
                        "platform": "aliexpress", 
                        "title": title, 
                        "url": link, 
                        "price": price, 
                        "discount": "0%", 
                        "rating": rating, 
                        "reviews": reviews
                    })
                except StaleElementReferenceException:
                    continue
                except Exception as e:
                    self.logger.warning(f"Error parsing AliExpress search result: {e}")
                    continue
                    
        except TimeoutException:
            self.logger.warning("AliExpress search results not found or took too long to load")
        except Exception as e:
            self.logger.error(f"Error processing AliExpress search results: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
            
        return results

    # -------------------- JUMIA --------------------
    def scrape_jumia(self):
        product_data = {"platform": "jumia", "url": self.driver.current_url}
        try:
            # Title
            try:
                title_elem = WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "h1.-fs20.-pts.-pbxs"))
                )
                product_data["title"] = title_elem.text.strip()
            except TimeoutException:
                product_data["title"] = "Not Found"

            # Price
            try:
                price_elem = self.driver.find_element(By.CSS_SELECTOR, "span.-b.-ltr.-tal.-fs24")
                product_data["price"] = price_elem.text.strip()
            except NoSuchElementException:
                product_data["price"] = "Not Found"

            # Discount
            try:
                discount_elem = self.driver.find_element(By.CSS_SELECTOR, "span.bdg._dsct._dyn.-mls")
                product_data["discount"] = discount_elem.text.strip()
            except NoSuchElementException:
                product_data["discount"] = "0%"

            # Rating
            try:
                rating_elem = self.driver.find_element(By.CSS_SELECTOR, "div.stars._m._al")
                rating_text = rating_elem.get_attribute("style")
                match = re.search(r"width:\s*(\d+)%", rating_text)
                product_data["rating"] = str(int(match.group(1)) / 20) if match else "Not Found"
            except NoSuchElementException:
                product_data["rating"] = "Not Found"

            # Reviews count
            try:
                reviews_elem = self.driver.find_element(By.CSS_SELECTOR, "a.-plxs._more")
                product_data["reviews"] = reviews_elem.text.split(" ")[0]
            except NoSuchElementException:
                product_data["reviews"] = "0"
                
        except Exception as e:
            self.logger.error(f"Error parsing Jumia product: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
            return None
            
        return product_data

    def scrape_jumia_search(self):
        results = []
        try:
            # Wait for search results
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "article.prd._fb.col.c-prd"))
            )
            
            items = self.driver.find_elements(By.CSS_SELECTOR, "article.prd._fb.col.c-prd")
            self.logger.info(f"Found {len(items)} search results on Jumia")
            
            for elem in items[:10]:
                try:
                    title = elem.find_element(By.CSS_SELECTOR, "h3.name").text
                    link = elem.find_element(By.CSS_SELECTOR, "a.core").get_attribute("href")
                    
                    try:
                        price = elem.find_element(By.CSS_SELECTOR, "div.prc").text
                    except NoSuchElementException:
                        price = "Not Found"
                        
                    try:
                        rating = elem.find_element(By.CSS_SELECTOR, "div.stars._s").text
                    except NoSuchElementException:
                        rating = "Not Found"
                        
                    try:
                        reviews = elem.find_element(By.CSS_SELECTOR, "div.rev").text
                    except NoSuchElementException:
                        reviews = "0"
                        
                    results.append({
                        "platform": "jumia", 
                        "title": title, 
                        "url": link, 
                        "price": price, 
                        "discount": "0%", 
                        "rating": rating, 
                        "reviews": reviews
                    })
                except StaleElementReferenceException:
                    continue
                except Exception as e:
                    self.logger.warning(f"Error parsing Jumia search result: {e}")
                    continue
                    
        except TimeoutException:
            self.logger.warning("Jumia search results not found or took too long to load")
        except Exception as e:
            self.logger.error(f"Error processing Jumia search results: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
            
        return results


if __name__ == "__main__":
    scraper = EcommerceScraper(headless=True)
    data = scraper.scrape_all_products()
    print(f"Scraped {len(data)} products")