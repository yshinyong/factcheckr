from flask import Flask, request, render_template
from openai import AzureOpenAI
import os
import fitz  # PyMuPDF
from PIL import Image
import pytesseract
import markdown
import io

app = Flask(__name__)

# ========== Azure OpenAI Configuration ==========

deployment_name = "gpt-4.1"

def get_openai_client():
    key = os.getenv("AZURE_OPENAI_KEY")
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")

    if not key or not endpoint:
        raise EnvironmentError("Missing AZURE_OPENAI_KEY or AZURE_OPENAI_ENDPOINT environment variables.")

    return AzureOpenAI(
        api_key=key,
        api_version="2024-12-01-preview",
        azure_endpoint=endpoint
    )

# Then inside your route or wherever needed:
client = get_openai_client()

# ========== System Prompt ==========
system_prompt = """
You are a Financial News Verification Assistant. When provided with a text input, image content, or URL (converted to text), perform the following analysis:

### 1. Credibility Score (1–5):
Evaluate the reliability of the source and the factual accuracy of the content.

Output format:
### Credibility Score (1 – 5):
- [score] out of 5

### 2. Misinformation Flags:
Identify and explain any potential:
- Contradictions with verified facts
- Exaggerations or sensationalism
- Use of manipulative or misleading language

Output as an unordered list:
### Misinformation Flags:
- [Flag 1]
- [Flag 2]

### 3. Sentiment Classification:
Determine the sentiment toward any mentioned companies or assets using one of the following labels:
Very Positive, Likely Positive, Neutral, Likely Negative, Negative

Output format:
### Sentiment:
- [Sentiment Label]

### 4. Summary:
Provide a concise summary of your overall assessment.

Output format:
### Summary:
- [Point 1]
- [Point 2]
- [Point 3]
"""

# ========== Helper: File Extraction ==========
def extract_text_from_file(file_storage):
    filename = file_storage.filename.lower()
    content = ""

    try:
        if filename.endswith(".txt"):
            content = file_storage.read().decode("utf-8")

        elif filename.endswith(".pdf"):
            with fitz.open(stream=file_storage.read(), filetype="pdf") as doc:
                content = "\n".join(page.get_text() for page in doc)

        elif filename.endswith((".png", ".jpg", ".jpeg")):
            image = Image.open(file_storage.stream)
            content = pytesseract.image_to_string(image)

        else:
            content = f"[Unsupported file type: {filename}]"

    except Exception as e:
        content = f"[Error extracting content from '{filename}': {e}]"

    return content

# ========== Routes ==========
@app.route("/", methods=["GET", "POST"])
def index():
    result_html = None
    user_input = ""

    if request.method == "POST":
        user_input = request.form.get("news_text", "").strip()
        uploaded_file = request.files.get("file")

        if uploaded_file and uploaded_file.filename:
            file_content = extract_text_from_file(uploaded_file)
            user_input += f"\n\n{file_content}"

        if user_input:
            try:
                response = client.chat.completions.create(
                    model=deployment_name,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_input}
                    ],
                    temperature=0.3
                )
                markdown_output = response.choices[0].message.content
                result_html = markdown.markdown(markdown_output, extensions=["extra", "nl2br"])

            except Exception as e:
                result_html = f"<p><strong>Error:</strong> {e}</p>"

    return render_template("index.html", response=result_html, input_text=user_input)

# ========== Run Locally ==========
if __name__ == "__main__":
    app.run(debug=os.getenv("FLASK_DEBUG", "false").lower() == "true", host="0.0.0.0", port=8000)
