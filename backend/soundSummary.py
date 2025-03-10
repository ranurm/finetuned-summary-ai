import os
import torch
from transformers import pipeline, WhisperProcessor
from moviepy import VideoFileClip

def extract_audio(video_file: str, output_audio: str = "temp_audio.wav") -> str:
    """Extracts audio from an MP4 file and saves it as WAV."""
    video = VideoFileClip(video_file)
    video.audio.write_audiofile(output_audio)
    return output_audio

def transcribe_audio(audio_file: str, chunk_length_s: int = 30) -> str:
    """Transcribes audio using Whisper with forced English language decoding."""
    try:
        temp_audio = None
        
        # Convert video to audio if needed
        if (audio_file.endswith(".mp4")):
            temp_audio = extract_audio(audio_file)
            audio_file = temp_audio
        
        # Load Whisper processor and set forced decoder IDs
        processor = WhisperProcessor.from_pretrained("openai/whisper-large-v2")
        forced_decoder_ids = processor.get_decoder_prompt_ids(language="en", task="transcribe")
        
        # Initialize Whisper pipeline
        device = "cuda:0" if torch.cuda.is_available() else "cpu"
        pipe = pipeline(
            "automatic-speech-recognition",
            model="openai/whisper-large-v2",
            device=device
        )
        
        # Perform transcription
        result = pipe(audio_file, chunk_length_s=chunk_length_s, generate_kwargs={"forced_decoder_ids": forced_decoder_ids})
        
        # Cleanup temporary file
        if temp_audio and os.path.exists(temp_audio):
            os.remove(temp_audio)
        
        return result["text"]
    except Exception as e:
        return f"Error processing file: {str(e)}"