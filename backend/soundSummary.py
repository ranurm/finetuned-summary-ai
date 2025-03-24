"""
Audio Extraction and Transcription Module

This module is responsible for:
- Extracting audio from video files (MP4)
- Transcribing speech to text using OpenAI's Whisper model
- Handling various error conditions during audio processing

The module provides robust audio processing with:
- Automatic fallback to smaller chunk sizes for difficult audio
- Verification of required dependencies (ffmpeg)
- Proper cleanup of temporary files
"""

import os
import torch
from transformers import pipeline, WhisperProcessor
from moviepy.editor import VideoFileClip
import logging

# Configure logging for this module
logger = logging.getLogger(__name__)

# Initialize Whisper speech recognition pipeline
try:
    # Set up English forced decoding (currently set to None, but could be configured)
    forced_decoder_ids = None
    
    # Initialize the transcription pipeline with Whisper small model
    # - chunk_length_s: Audio is processed in 30-second chunks for memory efficiency
    # - device: Uses CPU by default, but could use GPU if available
    pipe = pipeline(
        "automatic-speech-recognition",
        model="openai/whisper-small",
        chunk_length_s=30,
        device="cpu"
    )
    logger.info("Whisper pipeline initialized successfully")
except Exception as e:
    # Log error if model initialization fails
    logger.error(f"Error initializing Whisper pipeline: {str(e)}")

def extract_audio(video_file: str, output_audio: str = "temp_audio.wav") -> str:
    """
    Extracts audio track from an MP4 video file and saves it as a WAV file.
    
    This function uses MoviePy to:
    1. Load the video file
    2. Extract the audio track
    3. Save it to a WAV file for transcription
    
    Args:
        video_file (str): Path to the MP4 video file
        output_audio (str): Path where the extracted audio will be saved
                           (defaults to "temp_audio.wav")
        
    Returns:
        str: Path to the extracted audio file
    """
    # Load the video file using MoviePy
    video = VideoFileClip(video_file)
    
    # Extract audio track and save as WAV
    # Note: WAV format is used because it's uncompressed and widely supported
    video.audio.write_audiofile(output_audio)
    
    return output_audio

def transcribe_audio(audio_file: str, chunk_length_s: int = 30) -> str:
    """
    Transcribes audio using OpenAI's Whisper model with robust error handling.
    
    This function:
    1. Extracts audio if given a video file
    2. Checks for ffmpeg availability
    3. Processes audio through Whisper model
    4. Falls back to smaller chunks if initial transcription fails
    5. Cleans up temporary files
    
    Args:
        audio_file (str): Path to the audio or video file
        chunk_length_s (int): Length of audio chunks for processing (in seconds)
        
    Returns:
        str: Transcribed text or error message
    """
    # Initialize variables outside of try block to ensure they're available in finally
    temp_audio = None
    result = None
    
    try:
        # Check if input is a video file and extract audio if needed
        if (audio_file.endswith(".mp4")):
            logger.info(f"Extracting audio from video file: {audio_file}")
            temp_audio = extract_audio(audio_file)
            audio_file = temp_audio
        
        # Check if ffmpeg is available (required by Whisper for audio processing)
        try:
            import subprocess
            logger.info("Checking for ffmpeg availability...")
            ffmpeg_result = subprocess.run(['ffmpeg', '-version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            ffmpeg_available = ffmpeg_result.returncode == 0
        except (FileNotFoundError, subprocess.SubprocessError):
            ffmpeg_available = False
        
        # Return error if ffmpeg is not available
        if not ffmpeg_available:
            logger.error("FFmpeg not found. Please install FFmpeg and add it to your PATH.")
            return "Error: FFmpeg not found. Please install FFmpeg and add it to your PATH. See installation instructions at https://ffmpeg.org/download.html"
        
        # First transcription attempt with standard chunk size
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
            # Log error and try again with smaller chunk size
            logger.error(f"Error during transcription: {str(e)}")
            logger.info("Retrying with smaller chunk size...")
            
            # Second attempt with smaller chunk size (helps with complex audio)
            try:
                logger.info("Retrying with smaller chunk size...")
                result = pipe(
                    audio_file,
                    chunk_length_s=15,  # Half the original chunk size
                    generate_kwargs={"forced_decoder_ids": forced_decoder_ids},
                    return_timestamps=False
                )
                logger.info("Transcription completed successfully with smaller chunks")
                return result["text"]
            except Exception as e2:
                # If both attempts fail, log detailed error and re-raise
                logger.error(f"Error during second transcription attempt: {str(e2)}")
                raise

    except Exception as e:
        # Catch any other exceptions that might occur
        logger.error(f"Error in transcribe_audio: {str(e)}")
        return f"Error processing file: {str(e)}"
    finally:
        # Always clean up temporary files, even if an error occurred
        if temp_audio and os.path.exists(temp_audio):
            try:
                os.remove(temp_audio)
                logger.info("Temporary audio file removed")
            except Exception as e:
                logger.error(f"Error removing temporary file: {str(e)}")