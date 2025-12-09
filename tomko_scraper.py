import asyncio
import os
import io
import re
import json
import pandas as pd
from urllib.parse import urlparse
from playwright.async_api import async_playwright
import requests
from PIL import Image as PILImage
from openpyxl import Workbook


# --------------------------------------------------------
# Ensure folder structure exists
# --------------------------------------------------------
os.makedirs("data", exist_ok=True)
os.makedirs("images", exist_ok=True)


# --------------------------------------------------------
# Helper: Convert all images to PNG
# --------------------------------------------------------
def convert_to_png(image_bytes):
    try:
        img = PILImage.open(io.BytesIO(image_bytes))
        img = img.convert("RGB")
        output = io.BytesIO()
        img.save(output, format="PNG")
        return output.getvalue()
    except Exception:
        return image_bytes


# --------------------------------------------------------
# Extract sport/category/subcategory from URL
# --------------------------------------------------------
def parse_url_categories(url):
    """
    /shop/<sport>/<category>/<subcategory>/product-slug/
    """
    parts = [p for p in urlparse(url).path.split("/") if p]
    if "shop" in parts:
        i = parts.index("shop")
        sport = parts[i+1] if len(parts) > i+1 else ""
        category = parts[i+2] if len(parts) > i+2 else ""
        subcategory = parts[i+3] if len(parts) > i+3 else ""
        return sport, category, subcategory
    return "", "", ""


# --------------------------------------------------------
# Extract model codes like TN-PREM-RD
# --------------------------------------------------------
def extract_model_codes(text):
    pattern = r"[A-Za-z0-9]+(?:-[A-Za-z0-9]+)+"
    matches = re.findall(pattern, text)
    return " ; ".join(matches) if matches else ""


# --------------------------------------------------------
# Download image and convert to PNG
# --------------------------------------------------------
def download_image_as_png(url, idx):
    try:
        r = requests.get(url, timeout=15)
        if r.status_code != 200:
            return ""
        png_bytes = convert_to_png(r.content)
        outpath = f"images/product_{idx}.png"
        with open(outpath, "wb") as f:
            f.write(png_bytes)
        return outpath
    except:
        return ""


# --------------------------------------------------------
# Scrape individual product page
# --------------------------------------------------------
async def scrape_product(browser, url, idx):
    page = await browser.new_page()
    await page.goto(url, timeout=60000)

    title = ""
    if await page.query_selector("h1.product_title"):
        title = await page.inner_text("h1.product_title")

    # model codes from short description
    model_codes = ""
    if await page.query_selector("div.woocommerce-product-details__short-description"):
        desc = await page.inner_text("div.woocommerce-product-details__short-description")
        model_codes = extract_model_codes(desc)

    sport, category, subcategory = parse_url_categories(url)

    # main image
    img_url = ""
    img_path = ""
    img_el = await page.query_selector("img.wp-post-image")
    if img_el:
        img_url = await img_el.get_attribute("src")
        img_path = download_image_as_png(img_url, idx)

    await page.close()

    return {
        "ProductURL": url,
        "ProductName": title,
        "ModelCodes": model_codes,
        "Sport": sport,
        "Category": category,
        "Subcategory": subcategory,
        "ImageURL": img_url,
        "ImagePath": img_path
    }


# --------------------------------------------------------
# Scrape list page
# --------------------------------------------------------
async def scrape_list_page(page, url):
    await page.goto(url, timeout=60000)
    links = await page.eval_on_selector_all(
        "li.product a.woocommerce-LoopProduct-link",
        "els => els.map(e => e.href)"
    )
    return links


# --------------------------------------------------------
# Save all formats
# --------------------------------------------------------
def save_outputs(df):
    df.to_csv("data/tomko_products.csv", index=False)
    df.to_json("data/tomko_products.json", orient="records", indent=2)

    wb = Workbook()
    ws = wb.active
    ws.append(list(df.columns))
    for _, row in df.iterrows():
        ws.append(list(row.values))
    wb.save("data/tomko_products.xlsx")

    print("\nSaved:")
    print("- data/tomko_products.csv")
    print("- data/tomko_products.json")
    print("- data/tomko_products.xlsx")


# --------------------------------------------------------
# Main
# --------------------------------------------------------
async def main():
    MAX_PAGES = 30
    all_products = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        idx = 1
        for i in range(1, MAX_PAGES + 1):
            url = f"https://tomkosports.com/shop/page/{i}/"
            print(f"Scraping {url}...")

            links = await scrape_list_page(page, url)
            if not links:
                print("Reached final page.")
                break

            for link in links:
                print(f" → Product {idx}: {link}")
                data = await scrape_product(browser, link, idx)
                all_products.append(data)
                idx += 1

        await browser.close()

    df = pd.DataFrame(all_products)
    save_outputs(df)


if __name__ == "__main__":
    asyncio.run(main())
