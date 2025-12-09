import json
import numpy as np
from openai import OpenAI

client = OpenAI()

def build_nws_text(product):
    name = product.get("name", "")
    category = product.get("cat", "")
    subcategory = product.get("subcat", "")
    price = product.get("price", "")
    description = product.get("description", "")  # may not exist but safe

    text = f"""
    Name: {name}
    Category: {category}
    Subcategory: {subcategory}
    Price: {price}
    Description: {description}
    """

    return text.strip()

def create_nws_embeddings(input_json_path, output_npy_path):
    with open(input_json_path, "r") as f:
        data = json.load(f)

    embeddings = []
    for idx, product in enumerate(data):
        text = build_nws_text(product)

        print(f"Embedding NWS product {idx+1}/{len(data)}: {product.get('name')}")

        emb = client.embeddings.create(
            model="text-embedding-3-large",
            input=text
        ).data[0].embedding

        embeddings.append(emb)

    embeddings = np.array(embeddings)
    np.save(output_npy_path, embeddings)
    print(f"Saved NWS embeddings → {output_npy_path} with shape {embeddings.shape}")


if __name__ == "__main__":
    create_nws_embeddings(
        input_json_path="data/nws_products.json",
        output_npy_path="data/nws_embeddings.npy"
    )
