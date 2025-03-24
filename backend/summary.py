"""
FastAPI Backend Server for AI Meeting Summary Tool

This module serves as the main backend server using FastAPI to:
- Provide API endpoints for the frontend application
- Process both MP4 video files and PDF documents
- Orchestrate audio transcription, text extraction, and OCR
- Generate AI-powered summaries of meeting content
- Handle file uploads and manage temporary files

The server provides a RESTful API that the React frontend can interact with.
"""

import os
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from tempfile import NamedTemporaryFile
import uvicorn
import logging
import traceback

from slideSummary import extract_text_from_pdf, extract_images_and_ocr, generate_image_captions, askModel
from soundSummary import transcribe_audio

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI()
temp_files = []

# Add the CORS middleware to the FastAPI app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React app's URL
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allows all headers
)

@app.on_event("startup")
async def startup_event():
    """
    Event handler that runs when the FastAPI server starts.
    Logs startup information and any errors that occur during initialization.
    """
    try:
        logger.info("Starting up the server...")
    except Exception as e:
        logger.error(f"Error during startup: {str(e)}")
        logger.error(traceback.format_exc())
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """
    Event handler that runs when the FastAPI server shuts down.
    Logs shutdown event for monitoring and debugging purposes.
    """
    logger.info("Shutting down the server...")

@app.post("/generate_summary/")
async def api_generate_summary(mp4_file: UploadFile = File(None), pdf_file: UploadFile = File(None)):
    """
    API endpoint to process video and PDF files and generate a meeting summary.
    
    This function:
    1. Accepts uploaded MP4 and/or PDF files (both are optional)
    2. Processes video files to extract audio and transcribe speech
    3. Processes PDF files to extract text and analyze images
    4. Combines content from both sources for a comprehensive context
    5. Generates an AI summary using a fine-tuned model
    6. Cleans up temporary files regardless of outcome
    
    Args:
        mp4_file (UploadFile, optional): The uploaded MP4 video file
        pdf_file (UploadFile, optional): The uploaded PDF document
        
    Returns:
        dict: Response containing the summary or error information
              - summary: The generated text summary
              - status: "success" or "error"
              - message: Success confirmation or error details
    """
    try:
        # Initialize variables to store different types of extracted content
        transcription = ""       # Speech transcription from video
        pdf_text = ""            # Text extracted from PDF
        image_ocr_text = ""      # Text extracted from images in PDF via OCR
        image_captions_text = "" # AI-generated captions for images in PDF
        combined_context = ""    # Combined PDF content
        
        # === PROCESS VIDEO FILE ===
        if mp4_file:
            logger.info(f"Processing video file: {mp4_file.filename}")
            # Create a temporary file for the uploaded video
            with NamedTemporaryFile(delete=False, suffix=".mp4") as temp_file:
                temp_file.write(await mp4_file.read())
                temp_path = temp_file.name
                # Add to temp_files list for later cleanup
                temp_files.append(temp_path)

            # Extract audio and transcribe it to text
            transcription = transcribe_audio(temp_path)
            logger.info(f"Transcription generated: {len(transcription)} characters")

        # === PROCESS PDF FILE ===
        if pdf_file:
            logger.info(f"Processing PDF file: {pdf_file.filename}")
            # Create a temporary file for the uploaded PDF
            with NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
                temp_file.write(await pdf_file.read())
                temp_path = temp_file.name
                # Add to temp_files list for later cleanup
                temp_files.append(temp_path)

            # Extract text content directly from PDF
            pdf_text = extract_text_from_pdf(temp_path)
            
            # Extract text from images within the PDF using OCR
            image_ocr_text = extract_images_and_ocr(temp_path)
            
            # Generate captions for images within the PDF
            image_captions_text = generate_image_captions(temp_path)

            # Combine all PDF-derived content
            combined_context = f"{pdf_text}\n{image_ocr_text}\n{image_captions_text}"

        # === COMBINE CONTENT FROM ALL SOURCES ===
        meeting_content = ""
        # Format the content based on what was provided
        if transcription and combined_context:
            # Both video and PDF were provided
            meeting_content = f"Meeting Transcription:\n{transcription}\n\nMeeting Slides Content:\n{combined_context}"
        elif transcription:
            # Only video was provided
            meeting_content = f"Meeting Transcription:\n{transcription}"
        elif combined_context:
            # Only PDF was provided
            meeting_content = f"Meeting Slides Content:\n{combined_context}"
        else:
            # Neither video nor PDF was provided
            return {
                "summary": "",
                "status": "error",
                "message": "No content provided for summarization"
            }
        
        # === GENERATE SUMMARY ===
        # Set prompt for the AI model
        prompt = """
                You are an advanced AI assistant tasked with summarizing a meeting based on a transcript and meeting slides. Generate a structured summary using the following format:

                ##Meeting Summary##
                - Meeting Title: [Extract or summarize the title]
                - Attendants: [List key participants mentioned in the transcript or slides]
                - Date: [Extract the meeting date if available]

                ##1. Introduction##
                Provide a brief overview of the meeting, including its purpose and key objectives. Summarize why the meeting was held and any relevant background context.

                ##2. Key Discussion Points##
                Summarize the main topics discussed, focusing on essential details and any differing perspectives. Group related discussions into subtopics where applicable.

                ##3. Action Steps##
                List concrete action items, including:
                - What needs to be done
                - Who is responsible
                - Any deadlines or follow-up dates

                ##4. Conclusion##
                Summarize the key takeaways from the meeting, including final decisions and any closing remarks.

                **Instructions:**
                - Ensure clarity and conciseness.
                - Extract key insights without unnecessary details.
                - Structure the summary logically and professionally.
                - Use the given headlines as only headlines. List other text as bulletpoints
                - If certain information is missing from the input, indicate it clearly instead of making assumptions.
                """
        # Call the language model to generate the summary
        final_summary = askModel(prompt, meeting_content)
        logger.info(f"Final summary generated: {len(final_summary)} characters")

        # Return successful response with the generated summary
        return {
            "summary": final_summary,
            "status": "success",
            "message": "Summary generated successfully"
        }

    except Exception as e:
        # Log and return any errors that occur during processing
        logger.error(f"Error in generate_summary: {str(e)}")
        return {
            "summary": "",
            "status": "error",
            "message": str(e)
        }
    finally:
        # Cleanup all temporary files regardless of success or failure
        for temp_file in temp_files:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                    logger.debug(f"Removed temporary file: {temp_file}")
            except Exception as e:
                logger.error(f"Error removing temporary file {temp_file}: {str(e)}")

# Run FastAPI server
if __name__ == "__main__":
    try:
        logger.info("Initializing server...")
        
        # === CHECK PORT AVAILABILITY ===
        # Verify that port 8000 is not already in use
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('127.0.0.1', 8000))
        if result == 0:
            # Port is in use - log error and exit
            logger.error("Port 8000 is already in use!")
            raise RuntimeError("Port 8000 is already in use!")
        sock.close()
        
        # === START SERVER ===
        # Run the FastAPI application with uvicorn
        # reload=False for stability in production-like environments
        uvicorn.run(
            app,
            host="127.0.0.1",  # Only accessible from the local machine
            port=8000,         # Standard port for the backend API
            log_level="info"   # Match logging level with application
        )

    except Exception as e:
        # Log any startup errors
        logger.error(f"Failed to start server: {str(e)}")
        logger.error(traceback.format_exc())
        raise
