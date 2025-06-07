from flask import Flask, request, render_template
from openai import AzureOpenAI
import os
import fitz  # PyMuPDF for PDFs
from PIL import Image
import pytesseract
import markdown
import io

app = Flask(__name__)

# ========== Azure OpenAI Configuration ==========
client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_KEY"),
    api_version="2024-12-01-preview",
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
)
deployment_name = "gpt-4.1"

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

# ========== File Extraction Logic ==========
def extract_text_from_file(file_storage):
    filename = file_storage.filename.lower()
    content = ""

    try:
        if filename.endswith(".txt"):
            content = file_storage.read().decode("utf-8")

        elif filename.endswith(".pdf"):
            doc = fitz.open(stream=file_storage.read(), filetype="pdf")
            content = "\n".join(page.get_text() for page in doc)

        elif filename.endswith((".png", ".jpg", ".jpeg")):
            image = Image.open(file_storage.stream)
            content = pytesseract.image_to_string(image)

    except Exception as e:
        content = f"[Error extracting content: {e}]"

    return content

# ========== Flask Routes ==========
@app.route("/", methods=["GET", "POST"])
def index():
    result = None
    user_input = ""

    if request.method == "POST":
        user_input = request.form.get("news_text", "").strip()
        uploaded_file = request.files.get("file")

        # Append extracted file content
        if uploaded_file and uploaded_file.filename:
            extracted = extract_text_from_file(uploaded_file)
            user_input += f"\n\n{extracted}"

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

                markdown_text = response.choices[0].message.content
                result = markdown.markdown(markdown_text)

            except Exception as e:
                result = f"<p><strong>Error:</strong> {e}</p>"

    return render_template("index.html", response=result, input_text=user_input)

# ========== Run Server ==========
if __name__ == "__main__":
    app.run(debug=True)
