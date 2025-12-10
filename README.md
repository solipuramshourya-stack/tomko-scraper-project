# Tomko Sports Product Scraper & Competitor Matching Pipeline

This project builds an end-to-end pipeline to:  
1. Scrape Tomko Sports (Canadian retailer) product catalog  
2. Scrape competitor site (NetWorldSports)  
3. Extract brand/manufacturer info using heuristics + optional OCR  
4. Generate embeddings using MiniLM  
5. Match Tomko products against competitor products using cosine similarity  

This was developed as part of an academic project. The goal was to apply real-world data engineering and ML concepts while learning Python, scraping, and embeddings.

## Project Structure

tomko-scraper-project/
│
├── scrapers/
│   ├── tomko_scraper.py            # Scrapes Tomko Sports website
│   ├── nws_pipeline.py             # Scrapes NetWorldSports competitor site
│
├── enrichment/
│   ├── brand_enrichment.py         # Extracts & normalizes manufacturer/brand info
│
├── embeddings/
│   ├── create_embeddings.py        # Embeddings for Tomko products
│   ├── create_nws_embeddings.py    # Embeddings for NWS competitor products
│   ├── match_products.py           # Cosine similarity matching
│
├── data/
│   ├── tomko_products.json
│   ├── nws_products.json
│   ├── nws_tomko_matches.json
│
├── images/                         # for OCR
│
├── README.md
├── requirements.txt
└── .gitignore

## How to Run the Project

### 1. Install Dependencies

pip install -r requirements.txt


### 2. Scrape Tomko Products

python scrapers/tomko_scraper.py

Output → data/tomko_products.json

### 3.Scrape NetWorldSports Products

python scrapers/nws_pipeline.py
Output → `data/nws_products.json`

### 4.Manufacturer / Brand Enrichment

python enrichment/brand_enrichment.py
This extracts brand names using:
- Text parsing  
- Description scanning  
- Optional OCR for product images  

### 5.Create Embeddings

#### Tomko
python embeddings/create_embeddings.py
#### NWS competitor
python embeddings/create_nws_embeddings.py
Outputs saved in `/embeddings`

### 6.Match Products
python embeddings/match_products.py
Output → `data/nws_tomko_matches.json` -> This file contains competitor matches with similarity scores.

Note: OCR requires `tesseract` installed separately (optional).  

## Requirements

See `requirements.txt`.

This project was supported by coursework, online documentation, and AI-based debugging during development.  
All scraping performed for academic research purposes only (and was hopefully legal).

