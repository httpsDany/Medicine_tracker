from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import sqlite3
import time
import random

# ============= DB Setup =============
conn = sqlite3.connect('medicines.db')
cursor = conn.cursor()

# Drop old apollo table
cursor.execute("DROP TABLE IF EXISTS apollo")
conn.commit()

# Create updated apollo table (no packaging)
cursor.execute('''
    CREATE TABLE IF NOT EXISTS apollo (
        name TEXT,
        brand TEXT,
        price TEXT,
        discount TEXT,
        unit_price TEXT,
        source TEXT,
        UNIQUE(name, brand, source)
    )
''')
conn.commit()
print(" Reset table `apollo` successfully!")

# ============= User Agent Rotation =============
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) Gecko/20100101 Firefox/112.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.1 Safari/605.1.15",
]

# ============= Headless Browser Setup =============
options = Options()
options.add_argument("--headless=new")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument(f"user-agent={random.choice(USER_AGENTS)}")
driver = webdriver.Chrome(options=options)

# ============= Scrape One Medicine =============
def scrape_medicine(url):
    try:
        source = "apollo"
        driver.get(url)
        time.sleep(random.uniform(3, 6))
        soup = BeautifulSoup(driver.page_source, 'html.parser')

        # Extract fields
        try:
            name = soup.find('h1', class_="Jf").text.strip()
        except:
            name = None

        try:
            brand = soup.find('div', class_='Xl Yl').text.strip()
        except:
            brand = None

        try:
            price = soup.select_one('p[class*="rF_"]').text.strip()
        except:
            price = None

        '''try:
            mrp = soup.select_one('span[class*="sF_"]')
            if mrp_raw:
                mrp = mrp_raw.text.strip().replace("MRP ", "")
        except:
            mrp = None'''
        try:
            discount = soup.select_one('p[class*="tF_"]').text.strip()
        except:
            discount = None

        try:
            unit_price = soup.select_one('span.m.n').text.strip()
        except:
            unit_price = None

        cursor.execute('''
            INSERT OR IGNORE INTO apollo (name, brand, price, discount, unit_price, source)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (name, brand, price, discount, unit_price, source))
        conn.commit()

        print(f"[✓] Scraped: {name}")
    except Exception as e:
        print(f"[!] Error scraping {url}: {e}")

# ============= Search + Scrape Top Results =============
def search_and_scrape(keyword):
    search_url = f"https://www.apollopharmacy.in/search-medicines/{keyword}"
    driver.get(search_url)
    time.sleep(random.uniform(3, 6))

    product_links = []
    seen = set()

    try:
        cards = driver.find_elements(By.XPATH, "//a[contains(@href, '/otc/')]")
        for card in cards:
            href = card.get_attribute("href")
            if href and href not in seen:
                if href.startswith("/"):
                    full_url = "https://www.apollopharmacy.in" + href.split('?')[0]
                else:
                    full_url = href.split('?')[0]

                product_links.append(full_url)
                seen.add(href)
            if len(product_links) >= 5:
                break
    except Exception as e:
        print(f"[!] Error finding product links: {e}")

    print(f"\n🔍 Found {len(product_links)} results for '{keyword}':")
    for link in product_links:
        print(f"- {link}")
        scrape_medicine(link)

# ============= Run for List of Keywords =============
if __name__ == "__main__":
    keywords = [
    "paracetamol", "dolo 650", "combiflam", "zincovit", "calpol",
    "crocin", "azithromycin", "cetirizine", "sinarest", "metformin",
    "atorvastatin", "pantoprazole", "omeprazole", "amoxicillin",
    "aspirin", "ibuprofen", "diclofenac", "levocetirizine", "nimesulide",
    "benadryl", "dexorange", "liv 52", "zandu balm", "revital",
    "shelcal", "becosules", "neurobion forte", "eldecalcitol", "thyronorm",
    "losartan", "telmisartan", "ramipril", "cilnidipine", "glimepiride",
    "gliclazide", "pioglitazone", "linagliptin", "sitagliptin", "insulin"
]
    for med in keywords:
        search_and_scrape(med)

    driver.quit()
    conn.close()

