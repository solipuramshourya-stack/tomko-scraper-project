import json
import numpy as np
import openai
import os


# -------------------------------
# 1. Load API key from terminal
# -------------------------------
openai.api_key = os.getenv("OPENAI_API_KEY")

# -------------------------------
# 2. File paths for your project
# -------------------------------
TOMKO_JSON = "data/tomko_products.json"
NWS_JSON   = "data/nws_products.json"
TOMKO_EMB  = "data/tomko_embeddings.npy"

# -------------------------------
# 3. Load files
# -------------------------------
with open(TOMKO_JSON, "r") as f:
    tomko_data = json.load(f)

with open(NWS_JSON, "r") as f:
    nws_data = json.load(f)

tomko_embeddings = np.load(TOMKO_EMB)


# -------------------------------
# 4. Embed competitor products
# -------------------------------
def embed_text(text):
    """Uses OpenAI text-embedding-3-small without putting key in code."""
    resp = openai.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    return np.array(resp.data[0].embedding)


def competitor_text(p):
    """What part of competitor product to embed."""
    name = p.get("name", "")
    price = p.get("price", "")
    return f"{name}. Price {price}."


# Generate embeddings for all NWS products
nws_embeddings = []
for p in nws_data:
    nws_embeddings.append(embed_text(competitor_text(p)))

nws_embeddings = np.array(nws_embeddings)


# -------------------------------
# 5. MATCHING ENGINE
# TOMKO → NWS (client-first)
# -------------------------------
results = []


def cosine_sim(a, b):
    """Compute cosine similarity between 1 vector and matrix."""
    a_norm = a / np.linalg.norm(a)
    b_norm = b / np.linalg.norm(b, axis=1, keepdims=True)
    return np.dot(b_norm, a_norm)

for idx, tomko in enumerate(tomko_data):
    print(f"Matching Tomko SKU {idx+1}/{len(tomko_data)}: {tomko['ProductName']}")

    tomko_emb = tomko_embeddings[idx]
    sims = cosine_sim(tomko_emb, nws_embeddings)

    top3_idx = sims.argsort()[::-1][:3]

    matches = []
    for i in top3_idx:
        c = nws_data[i]
        matches.append({
            "CompetitorName": c["name"],
            "CompetitorPrice": c["price"],
            "CompetitorURL": c["url"],
            "Similarity": float(sims[i])
        })

    results.append({
        "TomkoProduct": tomko["ProductName"],
        "TomkoURL": tomko["ProductURL"],
        "Matches": matches
    })


# -------------------------------
# 6. Save results
# -------------------------------
with open("data/tomko_to_nws_matches.json", "w") as f:
    json.dump(results, f, indent=4)

print("\n🎉 Saved results → data/tomko_to_nws_matches.json")
