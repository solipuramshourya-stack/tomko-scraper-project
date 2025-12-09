import json
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options


BASE_URL = "https://www.networldsports.com/"
OUTPUT_FILE = "data/nws_products.json"


# ----------------------------------------------------------------
# INIT DRIVER (Desktop mode, JS hydration friendly)
# ----------------------------------------------------------------
def init_driver():
    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--window-size=1500,1200")
    options.add_argument("--disable-gpu")

    driver = webdriver.Chrome(options=options)
    driver.get(BASE_URL)

    # WAIT for hydration
    time.sleep(4)
    driver.execute_script("window.scrollTo(0, 300);")
    time.sleep(2)

    return driver


# ----------------------------------------------------------------
# GET TOP NAVIGATION CATEGORIES
# ----------------------------------------------------------------
def get_top_categories(driver):
    print("\n🔍 Extracting top categories...")

    # Desktop navigation wrapper
    nav_selectors = [
        "div.z-20.navigation a",         # main nav
        "nav a",                          # fallback
        "div.navigation a"                # fallback
    ]

    categories = []

    for sel in nav_selectors:
        try:
            items = driver.find_elements(By.CSS_SELECTOR, sel)
            for a in items:
                href = a.get_attribute("href")
                txt = a.text.strip()

                if not href or not txt:
                    continue

                txt_upper = txt.upper()

                # Skip non-sport menu items
                if txt_upper in ["HELP", "LOGIN", "ACCOUNT", "CART", "CHECKOUT"]:
                    continue
                if "black" in txt_upper.lower():
                    continue

                # only pick valid sports categories (you already know these)
                if any(sport in href for sport in [
                    "soccer", "tennis", "baseball", "cricket",
                    "basketball", "golf", "clothing"
                ]):
                    categories.append((txt_upper, href))

            if categories:
                break
        except:
            pass

    if not categories:
        raise Exception("❌ NAV NOT FOUND – hydration incomplete or selector mismatch")

    print(f"✅ Found categories: {[c[0] for c in categories]}")
    return categories


# ----------------------------------------------------------------
# GET SUBCATEGORY TILES (Equipment subcategories)
# ----------------------------------------------------------------
def get_subcategories(driver, category_url):
    print(f"\n📂 Loading category: {category_url}")
    driver.get(category_url)
    time.sleep(2)
    driver.execute_script("window.scrollTo(0, 400);")
    time.sleep(1)

    # subcategory tiles parent selectors
    selectors = [
        "div.sub-categories a",
        "div.sub-categories-mobile-list a",
        "a.item-title",
        "a[href*='.html']"
    ]

    subcats = []

    for sel in selectors:
        tiles = driver.find_elements(By.CSS_SELECTOR, sel)
        if len(tiles) >= 3:  # sanity check: equipment categories have 6-10 tiles
            for t in tiles:
                href = t.get_attribute("href")
                txt = t.text.strip()
                if href and txt:
                    subcats.append((txt, href))
            break

    print(f"   ➜ Found {len(subcats)} subcategories")
    return subcats

def extract_price(card):
    """
    Handles Hyvä (AlpineJS) dynamic prices seen in NWS PLP.
    We try multiple selectors because Hyvä changes classes based on sales.
    """

    selectors = [
        "span.text-base.font-semibold",            # primary sale/non-sale
        "span.price-wrapper",                      # wrapper used by Hyvä
        "[data-price-type='finalPrice'] .price",   # fallback
        "[data-price-type='finalPrice']",          # raw text
        ".price-container .price"                  # magento fallback
    ]

    for sel in selectors:
        try:
            el = card.find_element(By.CSS_SELECTOR, sel)
            txt = el.text.strip()
            if txt and "$" in txt:
                return txt
        except:
            continue

    # No price found → return N/A
    return "N/A"



# ----------------------------------------------------------------
# SCRAPE PLP PRODUCT LISTING PAGE
# ----------------------------------------------------------------
def scrape_plp(driver, plp_url, sub_category, category):
    print(f"\n🛒 Scraping PLP: {plp_url}")
    driver.get(plp_url)
    time.sleep(2)
    driver.execute_script("window.scrollTo(0, 300);")
    time.sleep(1)

    # product tile selectors
    selectors = [
        "li.item.product.product-item",
        "div.product-item-info",
        "li.product-item"
    ]

    tiles = []
    for sel in selectors:
        items = driver.find_elements(By.CSS_SELECTOR, sel)
        if len(items) > 0:
            tiles = items
            break

    print(f"   ➜ Found {len(tiles)} product tiles")

    products = []

    for item in tiles:
        try:
            # title
            name_el = item.find_element(By.CSS_SELECTOR, "a.product.photo.product-item-photo")
            name = name_el.get_attribute("title") or name_el.text.strip()

            # price
            price = extract_price(item)
            # url
            url = name_el.get_attribute("href")

            products.append({
                "name": name,
                "price": price,
                "url": url,
                "subcat":sub_category,
                "cat":category
            })
        except:
            continue

    print(f"   ✓ Parsed {len(products)} products\n")
    return products


# ----------------------------------------------------------------
# MAIN SCRAPER PIPELINE (2 Levels: Category → Subcategory → PLP)
# ----------------------------------------------------------------
def main():
    driver = init_driver()
    all_products = []
    SKIP_CATEGORIES = ["CLOTHING"]


    # 1. Get top categories
    categories = get_top_categories(driver)

    # 2. Traverse subcategories
    for cat_name, cat_url in categories:
        if cat_name.upper() in SKIP_CATEGORIES:
            print(f"\n⏭️ Skipping category: {cat_name}")
            continue

        print(f"\n==============================")
        print(f"   CATEGORY: {cat_name}")
        print(f"==============================")

        subcats = get_subcategories(driver, cat_url)

        for sub_name, sub_url in subcats:
            print(f"\n➡️ Subcategory: {sub_name}")
            products = scrape_plp(driver, sub_url, sub_name,cat_name)
            all_products.extend(products)
    driver.quit()

    # 4. Save output
    with open(OUTPUT_FILE, "w") as f:
        json.dump(all_products, f, indent=2)

    print(f"\n🎉 DONE! Total products scraped: {len(all_products)}")
    print(f"Saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
