import os
import torch
from transformers import pipeline, WhisperProcessor
from moviepy.editor import VideoFileClip
import logging

# Configure logging
logger = logging.getLogger(__name__)

# Initialize Whisper pipeline
try:
    # Set up English forced decoding
    forced_decoder_ids = None
    
    # Initialize the transcription pipeline
    pipe = pipeline(
        "automatic-speech-recognition",
        model="openai/whisper-small",
        chunk_length_s=30,
        device="cpu"
    )
    logger.info("Whisper pipeline initialized successfully")
except Exception as e:
    logger.error(f"Error initializing Whisper pipeline: {str(e)}")

def extract_audio(video_file: str, output_audio: str = "temp_audio.wav") -> str:
    """Extracts audio from an MP4 file and saves it as WAV."""
    video = VideoFileClip(video_file)
    video.audio.write_audiofile(output_audio)
    return output_audio

def transcribe_audio(audio_file: str, chunk_length_s: int = 30) -> str:
    """Transcribes audio using Whisper with forced English language decoding."""
    temp_audio = None
    result = None
    
    try:
        # Convert video to audio if needed
        if (audio_file.endswith(".mp4")):
            temp_audio = extract_audio(audio_file)
            audio_file = temp_audio
        
        # Check if ffmpeg is available
        try:
            import subprocess
            ffmpeg_result = subprocess.run(['ffmpeg', '-version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            ffmpeg_available = ffmpeg_result.returncode == 0
        except (FileNotFoundError, subprocess.SubprocessError):
            ffmpeg_available = False
        
        if not ffmpeg_available:
            logger.error("FFmpeg not found. Please install FFmpeg and add it to your PATH.")
            return "Error: FFmpeg not found. Please install FFmpeg and add it to your PATH. See installation instructions at https://ffmpeg.org/download.html"
        
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
                logger.info("Temporary audio file removed")
            except Exception as e:
                logger.error(f"Error removing temporary file: {str(e)}")