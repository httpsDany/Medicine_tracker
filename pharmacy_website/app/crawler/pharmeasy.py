import os
import time
import random
import sqlite3
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup

# ======================
# Database Setup
# ======================
conn = sqlite3.connect('medicines.db')
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS pharmeasy (
        name TEXT,
        brand TEXT,
        packaging TEXT,
        price TEXT,
        mrp TEXT,
        discount TEXT,
        unit_price TEXT,
        source TEXT,
        UNIQUE(name, brand, packaging, source)
    )
''')
conn.commit()

# ======================
# Progress Tracker Setup
# ======================
PROGRESS_FILE = "scraped.txt"
if os.path.exists(PROGRESS_FILE):
    with open(PROGRESS_FILE, "r") as f:
        completed_keywords = set(line.strip() for line in f)
else:
    completed_keywords = set()

# ======================
# Headless Chrome Setup
# ======================
options = Options()
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
driver = webdriver.Chrome(options=options)

# ======================
# Scrape Individual Product Page
# ======================
def scrape_medicine(url):
    try:
        source = "pharmeasy"
        driver.get(url)
        time.sleep(random.uniform(2, 4))  # Smart throttle
        soup = BeautifulSoup(driver.page_source, 'html.parser')

        name = soup.select_one('.MedicineOverviewSection_medicineName__9K61u')
        brand = soup.select_one('.MedicineOverviewSection_brandName__tyUH_')
        packaging = soup.select_one('.MedicineOverviewSection_measurementUnit__rPGh_')

        name = name.text.strip() if name else None
        brand = brand.text.replace("By", "").strip() if brand else None
        packaging = packaging.text.strip() if packaging else None

        price_tag = soup.select_one('.PriceInfo_ourPrice__A549p') or soup.select_one('.PriceInfo_unitPriceDecimal__i3Shz')
        price = price_tag.text.strip().replace("₹", "").strip() if price_tag else None
        if price:
            price = f"₹{price}"

        mrp_tag = soup.select_one('.PriceInfo_striked__fmcJv.PriceInfo_costPrice__jhiax')
        mrp = mrp_tag.text.strip() if mrp_tag else None

        discount_tag = soup.select_one('.PriceInfo_discountContainer__wTilO') or soup.select_one('.PriceInfo_gcdDiscountPercent__FvJsG')
        discount = discount_tag.text.strip() if discount_tag else None

        unit_price_tag = soup.select_one('.PriceInfo_originalMrp__TQJRs span') or soup.select_one('.PriceInfo_striked__fmcJv')
        unit_price = unit_price_tag.text.strip().replace("₹", "").strip() if unit_price_tag else None
        if unit_price and ("/" in unit_price):
            unit_price = f"₹{unit_price}"
        else:
            unit_price = None

        cursor.execute('''
            INSERT OR IGNORE INTO pharmeasy (name, brand, packaging, price, mrp, discount, unit_price, source)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (name, brand, packaging, price, mrp, discount, unit_price, source))
        conn.commit()

        print(f"[✓] Scraped: {name}")
    except Exception as e:
        print(f"[!] Error scraping {url}: {e}")

# ======================
# Search & Scrape Function
# ======================
def search_and_scrape(medicine_name):
    search_url = f"https://pharmeasy.in/search/all?name={medicine_name}"
    driver.get(search_url)
    time.sleep(random.uniform(2.5, 4))  # Smart throttle

    product_links = []
    seen = set()
    try:
        cards = driver.find_elements(By.XPATH, "//a[contains(@href, '/online-medicine-order/')]")
        for card in cards:
            href = card.get_attribute("href")
            if href and href not in seen and "/browse" not in href:
                product_links.append(href)
                seen.add(href)
            if len(product_links) >= 5:
                break
    except Exception as e:
        print(f"[!] Error finding product links for {medicine_name}: {e}")

    print(f"\n🔍 Found {len(product_links)} results for '{medicine_name}':")
    for link in product_links:
        print(f"- {link}")
        scrape_medicine(link)

# ======================
# Medicine Keyword List
# ======================
medicines_to_search = [
    "paracetamol", "dolo 650", "combiflam", "zincovit", "calpol",
    "crocin", "azithromycin", "cetirizine", "sinarest", "metformin",
    "atorvastatin", "pantoprazole", "omeprazole", "amoxicillin",
    "aspirin", "ibuprofen", "diclofenac", "levocetirizine", "nimesulide",
    "benadryl", "dexorange", "liv 52", "zandu balm", "revital",
    "shelcal", "becosules", "neurobion forte", "eldecalcitol", "thyronorm",
    "losartan", "telmisartan", "ramipril", "cilnidipine", "glimepiride",
    "gliclazide", "pioglitazone", "linagliptin", "sitagliptin", "insulin"
]
# ======================
# Run Scraper
# ======================
if __name__ == "__main__":
    try:
        for med in medicines_to_search:
            if med in completed_keywords:
                print(f"[→] Skipping already scraped: {med}")
                continue

            search_and_scrape(med)

            with open(PROGRESS_FILE, "a") as f:
                f.write(f"{med}\n")

            # Delay between keyword searches to avoid bot detection
            time.sleep(random.uniform(5, 8))

    finally:
        driver.quit()
        conn.close()

