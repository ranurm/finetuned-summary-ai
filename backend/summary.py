import os
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from tempfile import NamedTemporaryFile
import uvicorn

from slideSummary import extract_text_from_pdf, extract_images_and_ocr, generate_image_captions, ask_llama
from soundSummary import transcribe_audio

app = FastAPI()

# Add the CORS middleware to the FastAPI app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React app's URL
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allows all headers
)

@app.post("/transcribe_video/")
async def transcribe_video(file: UploadFile = File(...)):
    """API endpoint to receive a video file, transcribe its audio, and return the text."""
    try:
        # Save the uploaded video file temporarily
        with NamedTemporaryFile(delete=False, suffix=".mp4") as temp_file:
            temp_file.write(await file.read())
            temp_path = temp_file.name
        
        # Transcribe the audio  
        transcription = transcribe_audio(temp_path)
        
        # Remove the temporary video file
        os.remove(temp_path)
        
        return {"transcription": transcription}
    except Exception as e:
        return {"error": str(e)}

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