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
AZURE_OPENAI_KEY = os.getenv("AZURE_OPENAI_KEY")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
deployment_name = "gpt-4.1"

if not AZURE_OPENAI_KEY or not AZURE_OPENAI_ENDPOINT:
    raise EnvironmentError("Missing AZURE_OPENAI_KEY or AZURE_OPENAI_ENDPOINT environment variables.")

client = AzureOpenAI(
    api_key=AZURE_OPENAI_KEY,
    api_version="2024-12-01-preview",
    azure_endpoint=AZURE_OPENAI_ENDPOINT
)

# ========== System Prompt ==========
system_prompt = """
You are a Financial News Verification Assistant...

(CUT FOR BREVITY – keep your original prompt here)
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
