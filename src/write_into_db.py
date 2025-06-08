import pandas as pd
import ast
from pymongo import MongoClient
from pymongo.errors import PyMongoError
import os

# Load the CSV
df = pd.read_csv("../data/df_finfact_processed.csv")

# Convert the stringified embedding list to actual list
df['embedding'] = df['ada_v2'].apply(ast.literal_eval)

# Set up MongoDB connection
MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("MONGO_DB_NAME")
COLLECTION_NAME = os.getenv("MONGO_COLLECTION_NAME")

client = MongoClient(MONGO_URI)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]

# Prepare records
records = []

for _, row in df.iterrows():
    records.append({
        "text": row["text"],
        "claim": row["claim"],
        "url": row["url"],
        "n_tokens": row["n_tokens"],
        "embedding": row["embedding"]
        # You can include 'similarities' if it's meaningful here:
        # "similarities": row["similarities"]
    })

# Insert all at once
collection.insert_many(records)

print(f"Inserting {len(records)} records to {DB_NAME}.{COLLECTION_NAME}")
