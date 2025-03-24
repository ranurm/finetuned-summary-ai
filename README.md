# AI Meeting Summary Tool

An intelligent application that automatically generates concise, well-structured summaries from meeting recordings and presentation slides.

## Features

- **Video Processing**: Extract and transcribe audio from MP4 meeting recordings
- **PDF Analysis**: Extract text, perform OCR on images, and generate image captions from presentation slides
- **AI-Powered Summarization**: Generate comprehensive summaries using fine-tuned language models
- **Clean Formatting**: Present summaries with structured headings, bullet points, and organized sections
- **Modern UI**: Intuitive interface with drag-and-drop file uploads and real-time progress tracking
- **Multi-modal Analysis**: Combine insights from both audio and visual content for more comprehensive summaries

## Technologies Used

### Backend
- Python with FastAPI
- OpenAI fine-tuned models
- Whisper for audio transcription
- PyMuPDF and PyPDF2 for PDF processing
- Tesseract OCR for image text extraction
- BLIP for image captioning

### Frontend
- React.js
- Modern CSS with animations and responsive design

## Installation

### Prerequisites
- Python 3.9+
- Node.js and npm
- FFmpeg (for audio processing)
- Tesseract OCR

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/finetuned-summary-ai.git
   cd finetuned-summary-ai
   ```

2. Install backend dependencies:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   ```bash
   # Create a .env file in your project root
   # Add your OpenAI API key to the .env file
   # OPENAI_API_KEY=your_api_key_here
   ```

4. Install frontend dependencies:
   ```bash
   cd ..
   npm install
   ```

## Usage

### Starting the Application

Run both backend and frontend with a single command:
```bash
# On windows
start-app.bat

# On macOS or Linux
start-app-unix.sh
```

Or start them separately:
- Backend: `cd backend && python summary.py`
- Frontend: `npm start`

### Generating Summaries

1. Open your browser to [http://localhost:3000](http://localhost:3000)
2. Upload a meeting recording (MP4), presentation slides (PDF), or both
3. Click "Generate Summary"
4. View the formatted summary and copy it to your clipboard as needed

## Project Structure

```
finetuned-summary-ai/
├── backend/                # Python backend
│   ├── slideSummary.py     # PDF processing and summarization
│   ├── soundSummary.py     # Audio extraction and transcription
│   ├── summary.py          # FastAPI server and API endpoints
│   └── requirements.txt    # Python dependencies
├── src/                    # React frontend
│   ├── SummaryAI.js        # Main application component
│   ├── SummaryAI.css       # Styling
│   └── ...                 # Other React components
├── public/                 # Static assets
└── package.json            # npm configuration
```

## How It Works

1. **Input Processing**:
   - MP4 files: Audio is extracted and transcribed using Whisper
   - PDF files: Text is extracted, images are processed with OCR, and captions are generated

2. **Summarization**:
   - Content from audio transcription and PDF analysis is combined
   - A fine-tuned language model generates a structured summary
   - The summary is formatted with sections, bullet points, and hierarchical structure

3. **Presentation**:
   - The summary is displayed with clean formatting
   - Easy copying to clipboard for use in meeting notes or documentation

## Configuration

Adjust the application by modifying:
- `.env` file for API keys and other environment variables
- `backend/slideSummary.py` for summarization model parameters
- `backend/soundSummary.py` for transcription settings

## License

[MIT License](LICENSE)

## Acknowledgements

- OpenAI for the fine-tuned models, costs 3$ per 1 million tokens
- Salesforce for the BLIP image captioning model
- OpenAI for the Whisper speech recognition model
- The FastAPI and React communities for their excellent frameworks
