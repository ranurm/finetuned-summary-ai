import os
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from tempfile import NamedTemporaryFile
import uvicorn

from slideSummary import extract_text_from_pdf, extract_images_and_ocr, generate_image_captions, askModel
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

<<<<<<< Updated upstream
@app.post("/generate_summary/")
async def generate_summary(mp4_file: UploadFile = File(None), pdf_file: UploadFile = File(None)):
=======
@app.on_event("startup")
async def startup_event():
    """Log when the server starts up."""
    try:
        logger.info("Starting up the server...")
    except Exception as e:
        logger.error(f"Error during startup: {str(e)}")
        logger.error(traceback.format_exc())
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Log when the server shuts down."""
    logger.info("Shutting down the server...")

@app.post("/generate_summary/")
async def api_generate_summary(mp4_file: UploadFile = File(None), pdf_file: UploadFile = File(None)):
>>>>>>> Stashed changes
    """API endpoint to receive a video file and/or a PDF file, process them, and return a combined summary."""
    try:
        transcription = ""
        pdf_text = ""
        image_ocr_text = ""
        image_captions_text = ""
        combined_context = ""

        # Process video file if provided
        if mp4_file:
            logger.info(f"Processing video file: {mp4_file.filename}")
            with NamedTemporaryFile(delete=False, suffix=".mp4") as temp_file:
                temp_file.write(await mp4_file.read())
                temp_path = temp_file.name

            transcription = transcribe_audio(temp_path)
<<<<<<< Updated upstream
            print(f"Transcription generated: {len(transcription)} characters")
            os.remove(temp_path)
=======
            logger.info(f"Transcription generated: {len(transcription)} characters")
>>>>>>> Stashed changes

        # Process PDF file if provided
        if pdf_file:
            logger.info(f"Processing PDF file: {pdf_file.filename}")
            with NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
                temp_file.write(await pdf_file.read())
                temp_path = temp_file.name

            pdf_text = extract_text_from_pdf(temp_path)
            image_ocr_text = extract_images_and_ocr(temp_path)
            image_captions_text = generate_image_captions(temp_path)

            combined_context = f"{pdf_text}\n{image_ocr_text}\n{image_captions_text}"
<<<<<<< Updated upstream
            user_prompt = (
                "Combine the text given to you. They are from the same Teams meeting slides: "
                "one is the slide text, another is the slide pictures' text, and one contains captions "
                "generated for the pictures to help understand them better. "
                "Combine the texts into one paragraph. Do not add anything of your own."
            )
            pdf_summary = ask_llama(user_prompt, combined_context)
            print(f"PDF summary generated: {len(pdf_summary)} characters")
            os.remove(temp_path)
=======
>>>>>>> Stashed changes

        # Combine transcription and PDF content
        meeting_content = ""
        if transcription and combined_context:
            meeting_content = f"Meeting Transcription:\n{transcription}\n\nMeeting Slides Content:\n{combined_context}"
        elif transcription:
            meeting_content = f"Meeting Transcription:\n{transcription}"
        elif combined_context:
            meeting_content = f"Meeting Slides Content:\n{combined_context}"
        else:
            return {
                "summary": "",
                "status": "error",
                "message": "No content provided for summarization"
            }
        
<<<<<<< Updated upstream
        user_prompt = (
            "Combine the text given to you. They are from the same Teams meeting. One is the "
            "talking during the meeting, transcription, and one is the slides content PDF summary."
            "The talking is tiny bit more important than the slides. Combine the texts into one paragraph. "
        )
        final_summary = ask_llama(user_prompt, combined_summary)
        print(f"Final summary generated: {len(final_summary)} characters")
=======
        # Generate the summary using OpenAI's fine-tuned model
        prompt = "Please provide a concise summary of this meeting:"
        final_summary = askModel(prompt, meeting_content)
        logger.info(f"Final summary generated: {len(final_summary)} characters")
>>>>>>> Stashed changes

        return {
            "summary": final_summary,
            "status": "success",
            "message": "Summary generated successfully"
        }

    except Exception as e:
        logger.error(f"Error in generate_summary: {str(e)}")
        return {
            "summary": "",
            "status": "error",
            "message": str(e)
        }
<<<<<<< Updated upstream

# Run FastAPI server
if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
=======
    finally:
        # Cleanup all temporary files
        for temp_file in temp_files:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            except Exception as e:
                logger.error(f"Error removing temporary file {temp_file}: {str(e)}")

# Run FastAPI server
if __name__ == "__main__":
    try:
        logger.info("Initializing server...")
        # Check if port 8000 is available
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('127.0.0.1', 8000))
        if result == 0:
            logger.error("Port 8000 is already in use!")
            raise RuntimeError("Port 8000 is already in use!")
        sock.close()
        
        # Run without reload for simplicity
        uvicorn.run(
            app,
            host="127.0.0.1",
            port=8000,
            log_level="info"
        )

    except Exception as e:
        logger.error(f"Failed to start server: {str(e)}")
        logger.error(traceback.format_exc())
        raise
>>>>>>> Stashed changes
