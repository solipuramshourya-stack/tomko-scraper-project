import pandas as pd
import json
import re
import os
from difflib import get_close_matches
from paddleocr import PaddleOCR


# --------------------------------------------------------
# Initialize OCR (used only as final fallback)
# --------------------------------------------------------
ocr = PaddleOCR(
    lang='en',
    use_textline_orientation=True
)


# --------------------------------------------------------
# Verified Manufacturers (final list)
# --------------------------------------------------------
VERIFIED_BRANDS = [
    "Premier",
    "Douglas",
    "Jaypro",
    "Bison",
    "Gared Sports",
    "Porter Athletic",
    "First Team",
    "Jayhawk Bleachers",
    "Gill Athletics",
    "Champion Sports",
    "Cannon Sports",
    "MacGregor",
    "Rawlings",
    "Mikasa",
    "Brine",
    "Park & Sun",
    "Playmate",
    "Jugs Sports",
    "Vulcan Sporting Goods",
    "Nassau"
]

# Optional second-tier brands
SECONDARY_BRANDS = [
    "Steel Post Technologies",
    "Multi-Sport Pro",
    "ScorePro",
    "Advantage Sports",
    "GS Sports",
    "SwingNet"
]


# --------------------------------------------------------
# Prefix → Brand Mapping (verified)
# --------------------------------------------------------
PREFIX_TO_BRAND = {
    "PREM": "Premier",
    "DOUG": "Douglas",
    "JAYP": "Jaypro",
    "JAYPRO": "Jaypro",
    "BISON": "Bison",
    "GARED": "Gared Sports",
    "PORTER": "Porter Athletic",
    "FTEAM": "First Team",
    "FTMS": "First Team",
    "JHB": "Jayhawk Bleachers",
    "JHBY": "Jayhawk Bleachers",
    "GILL": "Gill Athletics",
    "CHAMP": "Champion Sports",
    "CANNON": "Cannon Sports",
    "MACGREGOR": "MacGregor",
    "RAWL": "Rawlings",
    "MIKASA": "Mikasa",
    "BRINE": "Brine",
    "PST": "Park & Sun",
    "PSUN": "Park & Sun",
    "PLMT": "Playmate",
    "JUGS": "Jugs Sports",
    "VULC": "Vulcan Sporting Goods",
    "NASSAU": "Nassau",
    "NASS": "Nassau",
    "SWNG": "SwingNet",
    "MSPRO": "Multi-Sport Pro",
    "SCP": "ScorePro",
    "ADV": "Advantage Sports",
    "GSS": "GS Sports",
    "STPT": "Steel Post Technologies",
    "STTPRO": "Steel Post Technologies",
    "STTPRE": "Steel Post Technologies",
    "STTPU": "Steel Post Technologies"
}


# --------------------------------------------------------
# Extract model-code prefixes
# --------------------------------------------------------
def extract_prefixes(model_codes):
    # Ensure safe type
    if not isinstance(model_codes, str):
        return []

    pattern = r"[A-Za-z0-9]+(?:-[A-Za-z0-9]+)+"
    matches = re.findall(pattern, model_codes)

    prefixes = []
    for code in matches:
        parts = code.split('-')
        if len(parts) >= 2:
            prefixes.append(parts[1].upper())

    return prefixes


# --------------------------------------------------------
# Fuzzy brand selection using prefix similarity
# --------------------------------------------------------
def fuzzy_brand(prefix):
    candidates = list(PREFIX_TO_BRAND.keys())
    match = get_close_matches(prefix, candidates, n=1, cutoff=0.7)
    if match:
        return PREFIX_TO_BRAND[match[0]], "medium", "fuzzy"
    return None, None, None


# --------------------------------------------------------
# OCR fallback — look for manufacturer in image text
# --------------------------------------------------------
def ocr_brand(image_path):
    if not image_path or not os.path.exists(image_path):
        return None, None, None
    try:
        result = ocr.ocr(image_path, cls=True)
        text = " ".join([line[1][0] for line in result[0]])
        text_upper = text.upper()
        for brand in VERIFIED_BRANDS + SECONDARY_BRANDS:
            if brand.upper() in text_upper:
                return brand, "low", "ocr"
    except:
        pass
    return None, None, None


# --------------------------------------------------------
# Main enrichment
# --------------------------------------------------------
def enrich_manufacturers(df):
    manufacturers = []
    prefixes_out = []
    confidence_out = []
    method_out = []

    for _, row in df.iterrows():
        model_codes = row["ModelCodes"]
        img_path = row["ImagePath"]

        prefixes = extract_prefixes(model_codes)
        prefixes_out.append(";".join(prefixes))

        # If no prefixes found
        if not prefixes:
            brand, conf, method = ocr_brand(img_path)
            manufacturers.append(brand if brand else "Unknown")
            confidence_out.append(conf or "low")
            method_out.append(method or "none")
            continue

        # Use most frequent prefix
        prefix_counts = {}
        for p in prefixes:
            prefix_counts[p] = prefix_counts.get(p, 0) + 1
        primary_prefix = max(prefix_counts, key=prefix_counts.get)

        # 1. Direct mapping
        if primary_prefix in PREFIX_TO_BRAND:
            brand = PREFIX_TO_BRAND[primary_prefix]
            manufacturers.append(brand)
            confidence_out.append("high")
            method_out.append("prefix")
            continue

        # 2. Fuzzy match
        brand, conf, method = fuzzy_brand(primary_prefix)
        if brand:
            manufacturers.append(brand)
            confidence_out.append(conf)
            method_out.append(method)
            continue

        # 3. OCR fallback
        brand, conf, method = ocr_brand(img_path)
        if brand:
            manufacturers.append(brand)
            confidence_out.append(conf)
            method_out.append(method)
            continue

        # 4. Unknown
        manufacturers.append("Unknown")
        confidence_out.append("low")
        method_out.append("none")

    df["Manufacturer"] = manufacturers
    df["ManufacturerPrefix"] = prefixes_out
    df["ManufacturerConfidence"] = confidence_out
    df["ManufacturerMethod"] = method_out
    return df


# --------------------------------------------------------
# Save files
# --------------------------------------------------------
def save_enriched(df):
    df.to_csv("data/enriched_products.csv", index=False)
    df.to_json("data/enriched_products.json", indent=2, orient="records")
    print("\nSaved enriched products to:")
    print(" - data/enriched_products.csv")
    print(" - data/enriched_products.json")


# --------------------------------------------------------
# Main execution
# --------------------------------------------------------
if __name__ == "__main__":
    df = pd.read_csv("data/tomko_products.csv")
    enriched = enrich_manufacturers(df)
    save_enriched(enriched)
