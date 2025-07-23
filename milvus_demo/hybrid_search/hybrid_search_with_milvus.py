#!/usr/bin/env python
# coding: utf-8

"""
# Hybrid Search with Dense and Sparse Vectors in Milvus

This script demonstrates how to conduct hybrid search with Milvus and BGE-M3 model. 
BGE-M3 model can convert text into dense and sparse vectors. Milvus supports storing 
both types of vectors in one collection, allowing for hybrid search that enhances 
the result relevance.

Milvus supports Dense, Sparse, and Hybrid retrieval methods:
- Dense Retrieval: Utilizes semantic context to understand the meaning behind queries.
- Sparse Retrieval: Emphasizes keyword matching to find results based on specific terms, equivalent to full-text search.
- Hybrid Retrieval: Combines both Dense and Sparse approaches, capturing the full context and specific keywords for comprehensive search results.

By integrating these methods, the Milvus Hybrid Search balances semantic and lexical similarities, 
improving the overall relevance of search outcomes.
"""

import os
import sys
import subprocess
import numpy as np
import pandas as pd
import time
from pymilvus import MilvusClient
from pymilvus import (
    connections,
    utility,
    FieldSchema,
    CollectionSchema,
    DataType,
    Collection,
)
from pymilvus.model.hybrid import BGEM3EmbeddingFunction
from pymilvus import AnnSearchRequest, WeightedRanker
import matplotlib.pyplot as plt
from typing import Dict, List, Any

# Install dependencies if not already installed
def install_requirements():
    try:
        import pymilvus
        print("PyMilvus is already installed.")
    except ImportError:
        print("Installing required packages...")
        subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "pymilvus", "\"pymilvus[model]\""])
        print("Packages installed successfully.")

# Download dataset if it doesn't exist
def download_dataset():
    dataset_path = "quora_duplicate_questions.tsv"
    if not os.path.exists(dataset_path):
        print("Downloading Quora Duplicate Questions dataset...")
        subprocess.run(["wget", "http://qim.fs.quoracdn.net/quora_duplicate_questions.tsv"])
        print("Dataset downloaded successfully.")
    else:
        print("Dataset already exists.")
    return dataset_path

# Load and prepare data
def load_data(dataset_path, num_samples=500):
    print("Loading and preparing data...")
    # Load the Quora dataset
    df = pd.read_csv(dataset_path, sep='\t')
    
    # Extract a sample of questions for our corpus
    questions = df['question1'].drop_duplicates().head(num_samples).tolist()
    
    print(f"Loaded {len(questions)} questions for the corpus.")
    return questions

# Set up BGE-M3 model for embedding generation
def setup_embedding_function():
    print("Setting up BGE-M3 embedding model...")
    ef = BGEM3EmbeddingFunction(use_fp16=False, device="cpu")
    dense_dim = ef.dim["dense"]
    print(f"BGE-M3 model loaded with dense dimension: {dense_dim}")
    return ef, dense_dim

# Generate embeddings for corpus
def generate_embeddings(embedding_function, corpus):
    print("Generating embeddings for corpus...")
    docs_embeddings = embedding_function(corpus)
    print("Embeddings generated successfully")
    return docs_embeddings

# Set up Milvus connection
def connect_to_milvus():
    # Using Milvus Lite for local development
    connections.connect(uri="./milvus.db")
    print("Connected to Milvus successfully!")

# Create a collection with dense and sparse vectors
def create_collection(dense_dim, collection_name="hybrid_demo"):
    # Drop the collection if it already exists
    if utility.has_collection(collection_name):
        Collection(collection_name).drop()
        print(f"Dropped existing collection: {collection_name}")

    # Create a collection that supports both dense and sparse vectors
    fields = [
        FieldSchema(
            name="pk", dtype=DataType.VARCHAR, is_primary=True, auto_id=True, max_length=100
        ),
        FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=512),
        FieldSchema(name="sparse_vector", dtype=DataType.SPARSE_FLOAT_VECTOR),
        FieldSchema(name="dense_vector", dtype=DataType.FLOAT_VECTOR, dim=dense_dim),
    ]
    schema = CollectionSchema(fields)
    col = Collection(collection_name, schema, consistency_level="Strong")
    
    # Create indices for efficient search
    sparse_index = {"index_type": "SPARSE_INVERTED_INDEX", "metric_type": "IP"}
    col.create_index("sparse_vector", sparse_index)
    dense_index = {"index_type": "AUTOINDEX", "metric_type": "IP"}
    col.create_index("dense_vector", dense_index)
    
    # Load collection to memory for searching
    col.load()
    
    print(f"Created and indexed collection: {collection_name}")
    return col

# Insert data into Milvus collection
def insert_data(collection, corpus, docs_embeddings):
    print("Inserting data into Milvus...")
    
    # Insert in batches for efficiency
    batch_size = 50
    for i in range(0, len(corpus), batch_size):
        end_idx = min(i + batch_size, len(corpus))
        batched_entities = [
            corpus[i:end_idx],
            docs_embeddings["sparse"][i:end_idx],
            docs_embeddings["dense"][i:end_idx],
        ]
        collection.insert(batched_entities)
    
    print(f"Inserted {collection.num_entities} records into Milvus.")

# Perform dense search (semantic search)
def dense_search(collection, query_embedding_dense, limit=5):
    print("Performing dense search...")
    
    search_params = {"metric_type": "IP", "params": {}}
    results = collection.search(
        [query_embedding_dense],
        anns_field="dense_vector",
        param=search_params,
        limit=limit,
        output_fields=["text"]
    )[0]
    
    return results

# Perform sparse search (keyword-based search)
def sparse_search(collection, query_embedding_sparse, limit=5):
    print("Performing sparse search...")
    
    search_params = {"metric_type": "IP", "params": {}}
    results = collection.search(
        [query_embedding_sparse],
        anns_field="sparse_vector",
        param=search_params,
        limit=limit,
        output_fields=["text"]
    )[0]
    
    return results

# Perform hybrid search (combining dense and sparse)
def hybrid_search(collection, query_embedding_dense, query_embedding_sparse, limit=5, sparse_weight=0.7, dense_weight=1.0):
    print("Performing hybrid search...")
    
    # Set up search requests for both dense and sparse vectors
    dense_search_params = {"metric_type": "IP", "params": {}}
    dense_req = AnnSearchRequest(
        [query_embedding_dense], "dense_vector", dense_search_params, limit=limit
    )
    
    sparse_search_params = {"metric_type": "IP", "params": {}}
    sparse_req = AnnSearchRequest(
        [query_embedding_sparse], "sparse_vector", sparse_search_params, limit=limit
    )
    
    # Combine results with weighted ranker
    rerank = WeightedRanker(sparse_weight, dense_weight)
    results = collection.hybrid_search(
        [sparse_req, dense_req], rerank=rerank, limit=limit, output_fields=["text"]
    )[0]
    
    return results

# Display search results in a formatted way
def display_results(search_results, search_type):
    if not search_results:
        print(f"No {search_type} search results found.")
        return []
    
    print(f"\n{search_type} Search Results:")
    print("-" * 80)
    
    results = []
    for i, hit in enumerate(search_results):
        text = hit.get("text")
        score = hit.get("score", hit.get("distance", 0))
        print(f"{i+1}. Score: {score:.4f} - {text}")
        results.append({"text": text, "score": score})
    
    return results

# Compare search results visually
def compare_search_methods(dense_results, sparse_results, hybrid_results, query_text):
    # Prepare data for visualization
    dense_scores = [res["score"] for res in dense_results]
    sparse_scores = [res["score"] for res in sparse_results]
    hybrid_scores = [res["score"] for res in hybrid_results]
    
    # Get texts (using hybrid results as they should contain the most relevant ones)
    texts = [res["text"] for res in hybrid_results]
    
    # Calculate number of results to show
    n_results = min(len(dense_results), len(sparse_results), len(hybrid_results), 5)
    if n_results == 0:
        print("No results to visualize.")
        return
    
    # Create bar chart
    fig, ax = plt.subplots(figsize=(14, 6))
    
    x = np.arange(n_results)
    bar_width = 0.25
    
    # Plot bars for each search method
    ax.bar(x - bar_width, dense_scores[:n_results], bar_width, label='Dense', color='blue', alpha=0.7)
    ax.bar(x, sparse_scores[:n_results], bar_width, label='Sparse', color='green', alpha=0.7)
    ax.bar(x + bar_width, hybrid_scores[:n_results], bar_width, label='Hybrid', color='red', alpha=0.7)
    
    # Add labels and legend
    ax.set_xlabel('Results')
    ax.set_ylabel('Relevance Score')
    ax.set_title(f'Comparison of Search Methods for Query: "{query_text}"')
    ax.set_xticks(x)
    ax.set_xticklabels([f"{i+1}" for i in range(n_results)])
    ax.legend()
    
    # Add text annotations under the chart
    plt.figtext(0.1, 0.01, 'Result texts:', wrap=True, fontsize=10, horizontalalignment='left')
    for i, text in enumerate(texts[:n_results]):
        if len(text) > 80:
            text = text[:77] + "..."
        plt.figtext(0.1, -0.02 - (i * 0.03), f"{i+1}. {text}", wrap=True, fontsize=8, horizontalalignment='left')
    
    plt.tight_layout()
    plt.subplots_adjust(bottom=0.2 + (n_results * 0.03))
    
    # Save figure
    plt.savefig('search_comparison.png')
    plt.show()
    
    print(f"Comparison chart saved to 'search_comparison.png'")

# Main function to run the entire process
def main():
    print("Starting Hybrid Search with Milvus demo...")
    
    # Install requirements
    install_requirements()
    
    # Download dataset
    dataset_path = download_dataset()
    
    # Load and prepare data
    corpus = load_data(dataset_path, num_samples=500)  # Using 500 questions for faster demo
    
    # Set up BGE-M3 model
    embedding_function, dense_dim = setup_embedding_function()
    
    # Generate embeddings for corpus
    docs_embeddings = generate_embeddings(embedding_function, corpus)
    
    # Connect to Milvus
    connect_to_milvus()
    
    # Create collection
    collection_name = "hybrid_demo"
    collection = create_collection(dense_dim, collection_name)
    
    # Insert data
    insert_data(collection, corpus, docs_embeddings)
    
    # Example query
    query_text = "How do I improve my programming skills?"
    print(f"\nPerforming search for query: '{query_text}'")
    
    # Generate embeddings for query
    query_embeddings = embedding_function([query_text])
    
    # Perform searches
    dense_results = dense_search(collection, query_embeddings["dense"][0])
    sparse_results = sparse_search(collection, query_embeddings["sparse"][[0]])
    hybrid_results = hybrid_search(
        collection, 
        query_embeddings["dense"][0],
        query_embeddings["sparse"][[0]],
        sparse_weight=0.7,
        dense_weight=1.0
    )
    
    # Display results
    dense_display = display_results(dense_results, "Dense")
    sparse_display = display_results(sparse_results, "Sparse")
    hybrid_display = display_results(hybrid_results, "Hybrid")
    
    # Compare search methods
    compare_search_methods(dense_display, sparse_display, hybrid_display, query_text)
    
    # Interactive mode
    while True:
        print("\n" + "=" * 80)
        user_query = input("\nEnter a search query (or 'q' to quit): ")
        if user_query.lower() == 'q':
            break
        
        # Generate embeddings for user query
        user_query_embeddings = embedding_function([user_query])
        
        # Perform searches with user query
        dense_results = dense_search(collection, user_query_embeddings["dense"][0])
        sparse_results = sparse_search(collection, user_query_embeddings["sparse"][[0]])
        hybrid_results = hybrid_search(
            collection, 
            user_query_embeddings["dense"][0],
            user_query_embeddings["sparse"][[0]],
            sparse_weight=0.7,
            dense_weight=1.0
        )
        
        # Display results
        dense_display = display_results(dense_results, "Dense")
        sparse_display = display_results(sparse_results, "Sparse")
        hybrid_display = display_results(hybrid_results, "Hybrid")
        
        # Compare search methods
        compare_search_methods(dense_display, sparse_display, hybrid_display, user_query)

if __name__ == "__main__":
    main() 