import os
import torch
from transformers import pipeline, WhisperProcessor
from moviepy.editor import VideoFileClip
from tempfile import NamedTemporaryFile
import logging

# Configure logging
logger = logging.getLogger(__name__)

# Initialize Whisper model globally
try:
    logger.info("Initializing Whisper model...")
    device = "cuda:0" if torch.cuda.is_available() else "cpu"
    logger.info(f"Using device: {device}")
    
    logger.info("Loading Whisper processor...")
    processor = WhisperProcessor.from_pretrained("openai/whisper-large-v2")
    forced_decoder_ids = processor.get_decoder_prompt_ids(language="en", task="transcribe")
    
    logger.info("Loading Whisper pipeline...")
    pipe = pipeline(
        "automatic-speech-recognition",
        model="openai/whisper-large-v2",
        device=device,
        torch_dtype=torch.float32  # Use float32 for better compatibility
    )
    logger.info("Whisper model initialized successfully")
except Exception as e:
    logger.error(f"Error initializing Whisper model: {str(e)}")
    raise

def extract_audio(video_file: str) -> str:
    """Extracts audio from an MP4 file and saves it as WAV."""
    try:
        with NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
            logger.info(f"Extracting audio from {video_file}")
            video = VideoFileClip(video_file)
            video.audio.write_audiofile(temp_file.name, verbose=False, logger=None)
            video.close()  # Explicitly close the video file
            logger.info("Audio extraction completed")
            return temp_file.name
    except Exception as e:
        logger.error(f"Error in extract_audio: {str(e)}")
        raise

def transcribe_audio(audio_file: str, chunk_length_s: int = 30) -> str:
    """Transcribes audio using Whisper with forced English language decoding."""
    temp_audio = None
    try:
        # Convert video to audio if needed
        if audio_file.endswith(".mp4"):
            temp_audio = extract_audio(audio_file)
            audio_file = temp_audio
        
        # Perform transcription with error handling
        try:
            logger.info("Starting transcription...")
            result = pipe(
                audio_file,
                chunk_length_s=chunk_length_s,
                generate_kwargs={"forced_decoder_ids": forced_decoder_ids},
                return_timestamps=False
            )
            logger.info("Transcription completed successfully")
            return result["text"]
        except Exception as e:
            logger.error(f"Error during transcription: {str(e)}")
            # Try with smaller chunk size if the first attempt fails
            try:
                logger.info("Retrying with smaller chunk size...")
                result = pipe(
                    audio_file,
                    chunk_length_s=15,  # Smaller chunk size
                    generate_kwargs={"forced_decoder_ids": forced_decoder_ids},
                    return_timestamps=False
                )
                logger.info("Transcription completed successfully with smaller chunks")
                return result["text"]
            except Exception as e2:
                logger.error(f"Error during second transcription attempt: {str(e2)}")
                raise

    except Exception as e:
        logger.error(f"Error in transcribe_audio: {str(e)}")
        return f"Error processing file: {str(e)}"
    finally:
        # Cleanup temporary file
        if temp_audio and os.path.exists(temp_audio):
            try:
                os.remove(temp_audio)
                logger.info("Temporary audio file cleaned up")
            except Exception as e:
                logger.error(f"Error removing temporary file: {str(e)}")