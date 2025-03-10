import os
import torch
import cv2
import numpy as np
import fitz  # PyMuPDF
import PyPDF2
import pytesseract
import uvicorn
from dotenv import load_dotenv
from PIL import Image
from transformers import BlipProcessor, BlipForConditionalGeneration
from groq import Groq
from google.colab import userdata
from fastapi import FastAPI, File, UploadFile
from tempfile import NamedTemporaryFile
#pip install torch opencv-python numpy pymupdf PyPDF2 pytesseract python-dotenv Pillow transformers groq fastapi uvicorn moviepy




# Initialize FastAPI app
app = FastAPI()

from fastapi.middleware.cors import CORSMiddleware

# Add the CORS middleware to the FastAPI app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React app's URL
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allows all headers
)

load_dotenv()
api_key = os.getenv("CROGAPI_KEY")

def extract_text_from_pdf(pdf_path):
    """Extracts text from a PDF file."""
    text = []
    with open(pdf_path, 'rb') as pdf_file:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        for page in pdf_reader.pages:
            extracted_text = page.extract_text()
            if extracted_text:
                text.append(extracted_text)
    return "\n".join(text)


def extract_images_and_ocr(pdf_path):
    """Extracts images from a PDF and performs OCR on them."""
    doc = fitz.open(pdf_path)
    all_text = []

    for page_num, page in enumerate(doc):
        images = page.get_images(full=True)

        for xref, *_ in images:
            img_data = doc.extract_image(xref)
            img_bytes = img_data["image"]

            np_array = np.frombuffer(img_bytes, np.uint8)
            img_cv = cv2.imdecode(np_array, cv2.IMREAD_COLOR)

            if img_cv is not None:
                text = pytesseract.image_to_string(img_cv)
                all_text.append(text)

    doc.close()
    return "\n\n".join(all_text)


def generate_image_captions(pdf_path, output_dir="extracted_images"):
    """Extracts images from a PDF and generates captions using BLIP."""
    os.makedirs(output_dir, exist_ok=True)
    device = "cuda" if torch.cuda.is_available() else "cpu"

    # Load BLIP model
    processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
    model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base").to(device)

    doc = fitz.open(pdf_path)
    image_paths = []

    for page_num, page in enumerate(doc):
        images = page.get_images(full=True)

        for img_index, (xref, *_) in enumerate(images):
            img_data = doc.extract_image(xref)
            img_bytes = img_data["image"]

            image_path = os.path.join(output_dir, f"page_{page_num + 1}_img_{img_index + 1}.jpg")
            with open(image_path, "wb") as f:
                f.write(img_bytes)

            image_paths.append(image_path)

    doc.close()

    captions = []
    for image_path in image_paths:
        image = Image.open(image_path).convert("RGB")
        inputs = processor(images=image, return_tensors="pt").to(device)
        output = model.generate(**inputs)
        caption = processor.decode(output[0], skip_special_tokens=True)
        captions.append(caption)

    return "\n".join(captions)


def ask_llama(prompt, context):
    """Sends a prompt to the Llama model and returns a response."""
    client = Groq(api_key=userdata.get('Crog_apikey'))
    response = client.chat.completions.create(
        messages=[{"role": "user", "content": f"{prompt} {context}"}],
        model="llama-3.3-70b-versatile"
    )
    return response.choices[0].message.content


@app.post("/process_pdf/")
async def process_pdf(file: UploadFile = File(...)):
    """API endpoint to receive a PDF file, process it, and return the summary."""
    try:
        # Save PDF temporarily
        with NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
            temp_file.write(await file.read())
            temp_path = temp_file.name

        # Extract content
        pdf_text = extract_text_from_pdf(temp_path)
        image_ocr_text = extract_images_and_ocr(temp_path)
        image_captions_text = generate_image_captions(temp_path)

        # Combine extracted data
        combined_context = f"{pdf_text}\n{image_ocr_text}\n{image_captions_text}"

        # Send to Llama for summarization
        user_prompt = (
            "Combine the text given to you. They are from the same Teams meeting slides: "
            "one is the slide text, another is the slide pictures' text, and one contains captions "
            "generated for the pictures to help understand them better. "
            "Combine the texts into one paragraph. Do not add anything of your own."
        )
        response = ask_llama(user_prompt, combined_context)

        # Remove temp file
        os.remove(temp_path)

        return {"summary": response}
    except Exception as e:
        return {"error": str(e)}

# Run FastAPI server
if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)