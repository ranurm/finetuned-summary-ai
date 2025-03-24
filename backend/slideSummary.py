"""
PDF Processing and AI Summarization Module

This module handles all PDF-related processing including:
- Text extraction from PDFs
- Image extraction and OCR processing
- Image caption generation
- Text summarization using fine-tuned language models

The module integrates several AI models:
- BLIP for image captioning
- Tesseract OCR for image text extraction
- OpenAI's fine-tuned models for text summarization
"""

import os
import torch
import cv2
import numpy as np
import fitz  # PyMuPDF for PDF processing
import PyPDF2  # Alternative PDF library for text extraction
import pytesseract  # OCR engine wrapper
from dotenv import load_dotenv
from PIL import Image
from transformers import BlipProcessor, BlipForConditionalGeneration, AutoTokenizer, AutoModelForSeq2SeqLM
import logging
import openai

# Configure logging for this module
logger = logging.getLogger(__name__)

# Load environment variables from .env file (contains API keys)
load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")
openai.api_key = openai_api_key

def extract_text_from_pdf(pdf_path):
    """
    Extracts text content from a PDF file.
    
    This function uses PyPDF2 to read the PDF and extract text from each page.
    Only text that's directly embedded in the PDF is extracted (not text in images).
    
    Args:
        pdf_path (str): Path to the PDF file
        
    Returns:
        str: Concatenated text from all pages of the PDF
    """
    text = []
    with open(pdf_path, 'rb') as pdf_file:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        for page in pdf_reader.pages:
            extracted_text = page.extract_text()
            if extracted_text:
                text.append(extracted_text)
    return "\n".join(text)

def extract_images_and_ocr(pdf_path):
    """
    Extracts images from a PDF and performs OCR to get text from those images.
    
    This function:
    1. Opens the PDF using PyMuPDF (fitz)
    2. Extracts embedded images from each page
    3. Converts image bytes to OpenCV format
    4. Performs OCR using Tesseract to extract text from images
    
    Args:
        pdf_path (str): Path to the PDF file
        
    Returns:
        str: Concatenated OCR text from all images in the PDF
    """
    doc = fitz.open(pdf_path)
    all_text = []

    for page_num, page in enumerate(doc):
        # Get all images on the current page
        images = page.get_images(full=True)

        for xref, *_ in images:
            # Extract the image data using its reference number (xref)
            img_data = doc.extract_image(xref)
            img_bytes = img_data["image"]

            # Convert image bytes to OpenCV format for processing
            np_array = np.frombuffer(img_bytes, np.uint8)
            img_cv = cv2.imdecode(np_array, cv2.IMREAD_COLOR)

            if img_cv is not None:
                # Perform OCR on the image to extract text
                text = pytesseract.image_to_string(img_cv)
                all_text.append(text)

    doc.close()
    return "\n\n".join(all_text)

def generate_image_captions(pdf_path, output_dir="extracted_images"):
    """
    Extracts images from a PDF and generates descriptive captions using the BLIP model.
    
    This function:
    1. Creates a directory to store extracted images if it doesn't exist
    2. Loads the BLIP image captioning model
    3. Extracts images from the PDF and saves them as JPG files
    4. Processes each image through BLIP to generate a natural language caption
    
    Args:
        pdf_path (str): Path to the PDF file
        output_dir (str): Directory to save extracted images
        
    Returns:
        str: Concatenated captions for all images in the PDF
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Determine if GPU is available, otherwise use CPU
    device = "cuda" if torch.cuda.is_available() else "cpu"

    # Load BLIP image captioning model
    processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
    model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base").to(device)

    # Open the PDF and extract images
    doc = fitz.open(pdf_path)
    image_paths = []

    for page_num, page in enumerate(doc):
        images = page.get_images(full=True)

        for img_index, (xref, *_) in enumerate(images):
            # Extract image data
            img_data = doc.extract_image(xref)
            img_bytes = img_data["image"]

            # Save the image to a file
            image_path = os.path.join(output_dir, f"page_{page_num + 1}_img_{img_index + 1}.jpg")
            with open(image_path, "wb") as f:
                f.write(img_bytes)
                
            image_paths.append(image_path)

    doc.close()

    # Generate captions for each extracted image
    captions = []
    for image_path in image_paths:
        # Open image and prepare it for the model
        image = Image.open(image_path).convert("RGB")
        inputs = processor(images=image, return_tensors="pt").to(device)
        
        # Generate caption
        output = model.generate(**inputs)
        caption = processor.decode(output[0], skip_special_tokens=True)
        captions.append(caption)

    return "\n".join(captions)

def generate_summary(prompt, context):
    """
    Generates a summary using a local fine-tuned model.
    
    This function uses a Hugging Face transformer model to generate a summary
    based on the provided prompt and context.
    
    NOTE: This appears to reference 'tokenizer' and 'model' variables that should
    be initialized elsewhere - this function may need to be updated to properly
    initialize these variables or handle their absence.
    
    Args:
        prompt (str): The summary request/instruction
        context (str): The text to be summarized
        
    Returns:
        str: Generated summary or error message
    """
    try:
        logger.info("Generating summary with fine-tuned model...")
        # Create input tokens for the model
        inputs = tokenizer(prompt + " " + context, return_tensors="pt", max_length=1024, truncation=True).to(device)
        
        # Generate summary with the model
        outputs = model.generate(**inputs, max_length=150, min_length=40, length_penalty=2.0, num_beams=4)
        summary = tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        logger.info("Summary generation completed")
        return summary
    except Exception as e:
        logger.error(f"Error generating summary: {str(e)}")
        return f"Error generating summary: {str(e)}"

def askModel(prompt, context):
    """
    Generates a summary using OpenAI's fine-tuned model via API.
    
    This is the primary summarization function that:
    1. Combines the user prompt and extracted content
    2. Sends a request to OpenAI's API using a custom fine-tuned model
    3. Returns the generated summary
    
    Args:
        prompt (str): Instruction for the AI (e.g., "Please summarize this meeting:")
        context (str): The combined text from transcription and PDF content
        
    Returns:
        str: The AI-generated summary or error message
    """
    try:
        logger.info("Generating summary with OpenAI fine-tuned model...")
        
        # Combine prompt and context into one message
        message_content = f"{prompt}\n\n{context}"
        
        # Call OpenAI API with the fine-tuned model
        # Note: This uses a specific fine-tuned model ID which is unique to this project
        response = openai.chat.completions.create(
            model="ft:gpt-4o-mini-2024-07-18:personal:capstone-10:BCiXe4PO",
            messages=[{"role": "user", "content": message_content}],
            temperature=0.7,  # Controls randomness (0=deterministic, 1=creative)
            max_tokens=16000  # Maximum length of the generated summary
        )
        
        # Extract and return the summary
        summary = response.choices[0].message.content
        logger.info("OpenAI summary generation completed")
        return summary
    except Exception as e:
        logger.error(f"Error generating OpenAI summary: {str(e)}")
        return f"Error generating summary: {str(e)}"
