import json
import numpy as np
from openai import OpenAI

client = OpenAI()

def build_tomko_text(product):
    name = product.get("ProductName", "")
    category = product.get("Category", "")
    subcategory = product.get("Subcategory", "")
    sport = product.get("Sport", "")
    model_codes = product.get("ModelCodes", "")
    
    # Tomko doesn't have long descriptions, but we still include empty field
    description = product.get("Description", "")

    text = f"""
    Name: {name}
    Category: {category}
    Subcategory: {subcategory}
    Sport: {sport}
    Model Codes: {model_codes}
    Description: {description}
    """

    return text.strip()

def create_tomko_embeddings(input_json_path, output_npy_path):
    with open(input_json_path, "r") as f:
        data = json.load(f)

    embeddings = []
    for idx, product in enumerate(data):
        text = build_tomko_text(product)

        print(f"Embedding Tomko product {idx+1}/{len(data)}: {product.get('ProductName')}")

        emb = client.embeddings.create(
            model="text-embedding-3-small",
            input=text
        ).data[0].embedding

        embeddings.append(emb)

    embeddings = np.array(embeddings)
    np.save(output_npy_path, embeddings)
    print(f"Saved Tomko embeddings → {output_npy_path} with shape {embeddings.shape}")


if __name__ == "__main__":
    create_tomko_embeddings(
        input_json_path="data/tomko_products.json",
        output_npy_path="data/tomko_embeddings.npy"
    )
