# Factcheckr AI

Factcheckr AI is a web-based app that allows users to input **financial news or text**, either by pasting text or uploading an image. The backend AI model analyzes the content and returns:

- ✅ **Credibility Score** (1–5)
- 🚨 **Misinformation Flags**
- 😐 **Sentiment Classification**

Refer to the factcheckrai_hackathon.pdf for more info!

---

## 🌐 Live Demo / Deployment

This app can be deployed to **Azure App Service** with minimal setup.

---

## 🚀 Getting Started (Run Locally)

### 1. Clone the Repository

```bash
git clone https://github.com/yshinyong/factcheckr.git
cd factcheckr
```

### 2. Create and Activate a Python Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
```
You should now see (venv) at the beginning of your terminal prompt.

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Set Environment Variables
Export the following environment variables (or set them in a .env file):
```bash
export AZURE_OPENAI_ENDPOINT="your_endpoint"
export AZURE_OPENAI_KEY="your_api_key"
```

### 5. Run the App Locally
```bash
python3 app.py
```
Visit the given URL to use the app.

## ☁️ Deploying to Azure App Service
To deploy this app to Azure App Service, ensure:

- You include gunicorn in your requirements.txt.

- Set the startup command in Azure App Settings:
```bash
gunicorn app:app --bind=0.0.0.0
````

- Set environment variables (AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_KEY) in the Azure App Service Configuration > Application settings.

## Others
### embedding
This Python script enables semantic search on financial fact-checking articles using Azure OpenAI's embedding models. What it Does:
- Processes finfact.json: Reads, cleans, and combines text data from the JSON file.
- Tokenizes & Filters: Counts text tokens and removes overly long documents.
- Generates Embeddings: Converts document text into numerical vectors using Azure OpenAI's text-embedding-ada-002 model.
- Performs Semantic Search: Calculates cosine similarity between a user query and document embeddings to find and return the most relevant articles.

After running the codes, save the embedding to Cosmos DB then use the saved data for fine-tuning GPT 4.1 model.

### write_into_db
This Python script is designed to ingest financial fact data, including their AI-generated embeddings, from a CSV file into a MongoDB database.