"""
startup.py — Entry point for Railway (and any cloud deployment).

This script runs BEFORE the Telegram bot starts:
  1. Creates / upgrades the SQLite database
  2. Builds the ChromaDB vector store (only if it doesn't exist yet)
  3. Launches the Telegram bot

This means you never have to manually run database.py or rag.py on the server.
Just deploy and everything sets up itself automatically.
"""

import os
import sys
import subprocess

print("=" * 55)
print("  AI SALES AGENT — STARTUP")
print("=" * 55)


# --------------------------------------------------
# Step 1: Setup SQLite database
# --------------------------------------------------

print("\n[1/3] Setting up database...")

from database import create_database
create_database()
print("      Database ready.")


# --------------------------------------------------
# Step 2: Build ChromaDB vector store (only if needed)
#
# We check if chroma_db/ already has content.
# On Railway with a mounted Volume, the chroma_db
# persists across deploys — so we skip rebuild
# unless product_info.txt has changed.
#
# To force a rebuild: delete chroma_db/ folder
# from the Railway volume and redeploy.
# --------------------------------------------------

print("\n[2/3] Checking RAG vector store...")

CHROMA_DIR = "chroma_db"
chroma_exists = (
    os.path.isdir(CHROMA_DIR)
    and any(
        fname.endswith(".sqlite3")
        for fname in os.listdir(CHROMA_DIR)
    )
)

if chroma_exists:
    print("      ChromaDB already exists — skipping rebuild.")
    print("      (Delete chroma_db/ folder to force a rebuild)")
else:
    print("      ChromaDB not found — building vector store...")
    print("      This takes ~30 seconds on first run...")

    # Run rag.py as a subprocess so it uses the same venv
    result = subprocess.run(
        [sys.executable, "rag.py"],
        capture_output=False  # show output in Railway logs
    )

    if result.returncode != 0:
        print("\n ERROR: RAG setup failed. Check logs above.")
        sys.exit(1)

    print("      ChromaDB vector store created successfully.")


# --------------------------------------------------
# Step 3: Start the Telegram bot
# --------------------------------------------------

print("\n[3/3] Starting Telegram bot...")
print("=" * 55)
print()

# Import and run directly (same process — Railway sees it as alive)
from telegram_bot import main
main()
