"""
rag.py — One-time setup script.

Run this ONCE to build the vector database from product_info.txt.

Usage:
    python rag.py

After running, the chroma_db/ folder will be created.
You do NOT need to run this again unless product_info.txt changes.
"""

import shutil
import os

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma


# --------------------------------------------------
# Step 1: Read the product knowledge file
# --------------------------------------------------

with open("data/product_info.txt", "r", encoding="utf-8") as file:
    text = file.read()

print("Product info loaded. Total characters:", len(text))


# --------------------------------------------------
# Step 2: Split text into chunks
#
# chunk_size=300  → smaller chunks = more precise retrieval
# chunk_overlap=30 → small overlap so context isn't lost at boundaries
# separators → split on double newlines first (section boundaries),
#              then single newlines, then sentences, then words
# --------------------------------------------------

splitter = RecursiveCharacterTextSplitter(
    chunk_size=300,
    chunk_overlap=30,
    separators=["\n\n", "\n", ". ", " ", ""]
)

chunks = splitter.create_documents([text])

print("Total chunks created:", len(chunks))

for i, chunk in enumerate(chunks):
    print(f"\n--- Chunk {i+1} ---")
    print(chunk.page_content)


# --------------------------------------------------
# Step 3: Create embeddings
# --------------------------------------------------

embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

print("\nEmbedding model loaded.")


# --------------------------------------------------
# Step 4: Delete old chroma_db and recreate fresh
#
# This avoids stale/duplicate chunks from previous runs.
# --------------------------------------------------

if os.path.exists("chroma_db"):
    shutil.rmtree("chroma_db")
    print("Old chroma_db deleted.")

vector_store = Chroma.from_documents(
    documents=chunks,
    embedding=embeddings,
    persist_directory="chroma_db"
)

print("\nVector database created successfully in chroma_db/")
print(f"Total chunks stored: {vector_store._collection.count()}")
print("You can now run telegram_bot.py or voice_agent.py")