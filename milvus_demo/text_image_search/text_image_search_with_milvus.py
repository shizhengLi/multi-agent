#!/usr/bin/env python
# coding: utf-8

"""
# Text-to-Image Search with Milvus

Text-to-image search is an advanced technology that allows users to search for images using natural language text
descriptions. It leverages a pretrained multimodal model to convert both text and images into embeddings in a shared
semantic space, enabling similarity-based comparisons.

In this tutorial, we will explore how to implement text-based image retrieval using OpenAI's CLIP (Contrastive
Language-Image Pretraining) model and Milvus. We will generate image embeddings with CLIP, store them in Milvus, and
perform efficient similarity searches.
"""

import os
import sys
import subprocess
import numpy as np
import time
import torch
from PIL import Image
import matplotlib.pyplot as plt
import glob
from pymilvus import connections, MilvusClient
import clip

# Install dependencies if not already installed
def install_requirements():
    try:
        import clip
        import pymilvus
        #from PIL import Image
        print("All required packages are already installed.")
    except ImportError:
        print("Installing required packages...")
        subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "pymilvus", "pillow"])
        subprocess.run([sys.executable, "-m", "pip", "install", "git+https://github.com/openai/CLIP.git"])
        print("Packages installed successfully.")

# Download example data if it doesn't exist
def download_example_data():
    if not os.path.exists("images_folder"):
        print("Downloading example data...")
        subprocess.run(["wget", "https://github.com/towhee-io/examples/releases/download/data/reverse_image_search.zip"])
        subprocess.run(["unzip", "-q", "reverse_image_search.zip", "-d", "images_folder"])
        print("Example data downloaded and extracted.")
    else:
        print("Example data already exists.")

# Set up Milvus connection
def connect_to_milvus():
    # Using Milvus Lite for local development
    milvus_client = MilvusClient(uri="milvus.db")
    print("Connected to Milvus successfully!")
    return milvus_client

# Load the CLIP model
def load_clip_model():
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model, preprocess = clip.load("ViT-B/32", device=device)
    print(f"Loaded CLIP model on {device}")
    return model, preprocess, device

# Define a function to encode images
def encode_image(image_path, model, preprocess, device):
    image = preprocess(Image.open(image_path)).unsqueeze(0).to(device)
    with torch.no_grad():
        image_features = model.encode_image(image)
    image_features /= image_features.norm(dim=-1, keepdim=True)  # Normalize the image features
    return image_features.cpu().squeeze().tolist()

# Define a function to encode text
def encode_text(text, model, device):
    text_tokens = clip.tokenize([text]).to(device)
    with torch.no_grad():
        text_features = model.encode_text(text_tokens)
    text_features /= text_features.norm(dim=-1, keepdim=True)  # Normalize the text features
    return text_features.cpu().squeeze().tolist()

# Create Milvus collection
def create_collection(milvus_client, collection_name):
    # Drop the collection if it already exists
    if milvus_client.has_collection(collection_name):
        milvus_client.drop_collection(collection_name)
        print(f"Dropped existing collection: {collection_name}")

    # Create a new collection in quickstart mode
    milvus_client.create_collection(
        collection_name=collection_name,
        dimension=512,  # this should match the dimension of the image embedding
        auto_id=True,   # auto generate id and store in the id field
        enable_dynamic_field=True,  # enable dynamic field for scalar fields
    )
    print(f"Created new collection: {collection_name}")

# Insert images into Milvus
def insert_images(milvus_client, collection_name, model, preprocess, device):
    image_dir = "./images_folder/train"
    raw_data = []

    # Get all JPEG images in the directory
    image_paths = glob.glob(os.path.join(image_dir, "**/*.JPEG"), recursive=True)
    total_images = len(image_paths)
    print(f"Processing {total_images} images...")

    for i, image_path in enumerate(image_paths):
        if i % 100 == 0:
            print(f"Processing image {i+1}/{total_images}")
        try:
            image_embedding = encode_image(image_path, model, preprocess, device)
            image_dict = {"vector": image_embedding, "filepath": image_path}
            raw_data.append(image_dict)
        except Exception as e:
            print(f"Error processing image {image_path}: {str(e)}")
    
    if raw_data:
        insert_result = milvus_client.insert(collection_name=collection_name, data=raw_data)
        print(f"Inserted {insert_result['insert_count']} images into Milvus.")
    else:
        print("No images were processed successfully.")

# Search for similar images based on text query
def search_by_text(milvus_client, collection_name, query_text, model, device, limit=10):
    query_embedding = encode_text(query_text, model, device)
    
    search_results = milvus_client.search(
        collection_name=collection_name,
        data=[query_embedding],
        limit=limit,  # return top N results
        output_fields=["filepath"],  # return the filepath field
    )
    
    return search_results

# Visualize search results
def visualize_results(search_results, query_text):
    if not search_results or not search_results[0]:
        print("No results found.")
        return
    
    # Calculate grid dimensions
    num_images = min(10, len(search_results[0]))
    cols = min(5, num_images)
    rows = (num_images + cols - 1) // cols  # Ceiling division
    
    # Create figure for plotting
    plt.figure(figsize=(15, 3 * rows))
    
    print(f"Query text: '{query_text}'")
    print(f"Top {num_images} search results:")
    
    # Plot each result
    for i, hit in enumerate(search_results[0][:num_images]):
        filename = hit["entity"]["filepath"]
        img = Image.open(filename)
        
        # Display in grid
        plt.subplot(rows, cols, i + 1)
        plt.imshow(img)
        plt.title(f"Score: {hit['distance']:.4f}")
        plt.axis('off')
    
    plt.tight_layout()
    plt.savefig('search_results.png')
    plt.show()
    
    print(f"Results saved to 'search_results.png'")

# Main function to run the entire process
def main():
    print("Starting Text-to-Image Search with Milvus demo...")
    
    # Install requirements
    install_requirements()
    
    # Download example data
    download_example_data()
    
    # Connect to Milvus
    milvus_client = connect_to_milvus()
    
    # Load CLIP model
    model, preprocess, device = load_clip_model()
    
    # Create collection
    collection_name = "image_collection"
    create_collection(milvus_client, collection_name)
    
    # Insert images
    insert_images(milvus_client, collection_name, model, preprocess, device)
    
    # Perform a search
    query_text = "a white dog"
    search_results = search_by_text(milvus_client, collection_name, query_text, model, device)
    
    # Visualize results
    visualize_results(search_results, query_text)
    
    # Interactive mode for user queries
    while True:
        user_query = input("\nEnter a text query (or 'q' to quit): ")
        if user_query.lower() == 'q':
            break
        
        search_results = search_by_text(milvus_client, collection_name, user_query, model, device)
        visualize_results(search_results, user_query)

if __name__ == "__main__":
    main() 