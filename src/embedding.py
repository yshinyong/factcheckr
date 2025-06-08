import os
import re
import pandas as pd
import numpy as np
import tiktoken
from openai import AzureOpenAI

pd.options.mode.chained_assignment = None #https://pandas.pydata.org/pandas-docs/stable/user_guide/indexing.html#evaluation-order-matters

# Load the finfact.json file
df = pd.read_json('data/finfact.json')

# Combine 'claim', 'sci_digest', and 'justification' into a new 'text' column
# Ensure 'sci_digest' is handled correctly if it's a list (join its elements)
df['sci_digest_str'] = df['sci_digest'].apply(lambda x: ' '.join(x) if isinstance(x, list) else x)
df['text'] = df['claim'] + " " + df['sci_digest_str'] + " " + df['justification']

# Select relevant columns for the new dataframe
df_finfact_processed = df[['text', 'claim', 'url']] # Keeping 'claim' and 'url' for context/display if needed

# s is input text
def normalize_text(s, sep_token = " \n "):
    s = str(s) # Ensure the input is a string
    s = re.sub(r'\s+', ' ', s).strip()
    s = re.sub(r". ,","",s)
    # remove all instances of multiple spaces
    s = s.replace("..",".")
    s = s.replace(". .",".")
    s = s.replace("\n", "")
    s = s.strip()
    return s

df_finfact_processed['text'] = df_finfact_processed["text"].apply(lambda x : normalize_text(x))

tokenizer = tiktoken.get_encoding("cl100k_base")
df_finfact_processed['n_tokens'] = df_finfact_processed["text"].apply(lambda x: len(tokenizer.encode(x)))
df_finfact_processed = df_finfact_processed[df_finfact_processed.n_tokens < 8192]
print(f"Number of documents after token filtering: {len(df_finfact_processed)}")

client = AzureOpenAI(
    api_key = os.getenv("AZURE_OPENAI_EMBED_API_KEY"),
    api_version = "2024-02-01",
    azure_endpoint = os.getenv("AZURE_OPENAI_EMBED_ENDPOINT")
)

def generate_embeddings(text, model="text-embedding-3-small"): # model = "deployment_name"
    return client.embeddings.create(input = [text], model=model).data[0].embedding

print("Generating embeddings. This may take some time...")
df_finfact_processed['ada_v2'] = df_finfact_processed["text"].apply(lambda x : generate_embeddings(x, model = 'text-embedding-3-small')) # model should be set to the deployment name you chose when you deployed the text-embedding-ada-002 (Version 2) model
print("Embeddings generated.")

def cosine_similarity(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

def get_embedding(text, model="text-embedding-3-small"): # model = "deployment_name"
    return client.embeddings.create(input = [text], model=model).data[0].embedding

def search_docs(df, user_query, top_n=4, to_print=True):
    embedding = get_embedding(
        user_query,
        model="text-embedding-3-small" 
    )
    df["similarities"] = df.ada_v2.apply(lambda x: cosine_similarity(x, embedding))

    res = (
        df.sort_values("similarities", ascending=False)
        .head(top_n)
    )
    if to_print:
        print(res[['claim', 'url', 'similarities']]) # Display relevant columns for search results
    return res

# Example search query relevant to the finfact.json data
res = search_docs(df_finfact_processed, "Is there a claim about Biden's views on shareholder capitalism?", top_n=4)

df_finfact_processed.to_csv("df_finfact_processed.csv", index=False, encoding="utf-8")
