import React, { useState, useRef, useEffect } from 'react';
import './SummaryAI.css';

/**
 * AI Meeting Summary Tool - Main Component
 * 
 * This component provides a user interface for:
 * - Uploading MP4 meeting recordings and PDF presentations
 * - Sending files to the backend for processing
 * - Displaying formatted summaries
 * - Tracking progress during summary generation
 * - Providing feedback for errors and successful operations
 */
function SummaryAI() {
  // ===== STATE MANAGEMENT =====
  // File state - tracks the uploaded files
  const [mp4File, setMp4File] = useState(null);
  const [pdfFile, setPdfFile] = useState(null);
  
  // UI state - controls various UI elements and feedback
  const [summary, setSummary] = useState('');      // The generated summary content
  const [loading, setLoading] = useState(false);   // Whether a summary is being generated
  const [error, setError] = useState(null);        // Error messages to display
  const [copied, setCopied] = useState(false);     // Whether summary was copied to clipboard
  const [dragActive, setDragActive] = useState({ mp4: false, pdf: false }); // Drag state for file uploads
  const [progress, setProgress] = useState(0);     // Progress bar percentage (0-100)
  
  // References to DOM elements
  const mp4InputRef = useRef(null);  // Reference to the MP4 file input
  const pdfInputRef = useRef(null);  // Reference to the PDF file input
  const summaryRef = useRef(null);   // Reference to the summary section for scrolling
  
  // ===== EFFECTS =====
  /**
   * Progress animation effect - simulates progress during loading
   * Since we don't have real-time progress updates from the backend,
   * this creates a visual indication that work is happening.
   */
  useEffect(() => {
    let interval;
    if (loading) {
      interval = setInterval(() => {
        setProgress((prev) => {
          // Slowly increase progress to 90% (the real progress is unknown)
          // We stop at 90% and only go to 100% when the response is received
          if (prev < 90) {
            return prev + (90 - prev) * 0.05;
          }
          return prev;
        });
      }, 500);
    } else {
      setProgress(0);
    }
    
    // Cleanup interval on unmount or when loading state changes
    return () => clearInterval(interval);
  }, [loading]);
  
  // ===== FILE HANDLING =====
  /**
   * Handles MP4 file selection from the file input
   * Validates that the file is actually an MP4 before setting state
   */
  const handleMp4FileChange = (e) => {
    const file = e.target.files?.[0];
    if (file && file.type === 'video/mp4') {
      setMp4File(file);
      setError(null);
    } else if (file) {
      setError('Please select a valid MP4 file');
    }
  };

  /**
   * Handles PDF file selection from the file input
   * Validates that the file is actually a PDF before setting state
   */
  const handlePdfFileChange = (e) => {
    const file = e.target.files?.[0];
    if (file && file.type === 'application/pdf') {
      setPdfFile(file);
      setError(null);
    } else if (file) {
      setError('Please select a valid PDF file');
    }
  };
  
  // ===== DRAG AND DROP FUNCTIONALITY =====
  /**
   * Handles drag events (enter, over, leave) for the file upload areas
   * Updates visual feedback when files are dragged over drop zones
   */
  const handleDrag = (e, type, active) => {
    e.preventDefault();
    e.stopPropagation();
    
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive({ ...dragActive, [type]: true });
    } else if (e.type === 'dragleave') {
      setDragActive({ ...dragActive, [type]: false });
    }
  };
  
  /**
   * Handles file drop events for the drag and drop zones
   * Validates file types and updates state accordingly
   */
  const handleDrop = (e, type) => {
    e.preventDefault();
    e.stopPropagation();
    
    setDragActive({ ...dragActive, [type]: false });
    
    const file = e.dataTransfer.files?.[0];
    if (!file) return;
    
    if (type === 'mp4' && file.type === 'video/mp4') {
      setMp4File(file);
      setError(null);
    } else if (type === 'pdf' && file.type === 'application/pdf') {
      setPdfFile(file);
      setError(null);
    } else {
      setError(`Please drop a valid ${type.toUpperCase()} file`);
    }
  };
  
  // ===== SUMMARY FORMATTING =====
  /**
   * Formats the plain text summary into structured HTML
   * Converts various patterns in the text to formatted HTML elements:
   * - Main section headers (1. Introduction:) become <h3> elements
   * - Sub-section headers become styled spans
   * - Bullet points become <li> elements in <ul> lists
   * - Numbered items become <li> elements in <ol> lists
   */
  const formatSummary = (text) => {
    if (!text) return '';
    
    // Remove "Meeting Summary" from the beginning if it exists
    let processedText = text.replace(/^Meeting Summary\s*\n+/i, '');
    
    // First handle main section headers (like "1. Introduction/Purpose:")
    const mainSectionFormatted = processedText.replace(/(\d+)\.\s+(.*?):/g, '<h3 class="summary-main-section"><span class="section-number">$1.</span> $2:</h3>');
    
    // Handle sub-section headers (colons at the end of a line - usually sub-topics)
    // Match only at the beginning of a line or after a newline, and make sure they're standalone headers
    const subSectionFormatted = mainSectionFormatted.replace(/^([^<\n][^:]+):((?=\s*$|\s+[A-Z]))/gm, '<span class="summary-sub-section">$1:</span>$2');
    
    // Handle sub-sub-section headers that have text after them (like "Reflected XSS via AJAX: Uses crafted links...")
    // Replace with inline bold style, keeping the same font size
    const subSubSectionFormatted = subSectionFormatted.replace(/^([^<\n][^:]+):(\s+)([^<\n])/gm, '<span class="summary-sub-sub-section">$1:</span>$2$3');
    
    // Replace **Headline** with styled headline (if any remain)
    const headlineFormatted = subSubSectionFormatted.replace(/\*\*(.*?)\*\*/g, '<h3 class="summary-headline">$1</h3>');
    
    // Enhance bullet points and numbered lists
    const bulletFormatted = headlineFormatted.replace(/- (.*?)(?=\n|$)/g, '<li class="summary-bullet">$1</li>');
    const numberedFormatted = bulletFormatted.replace(/^(?!\d+\.\s+.*:)(\d+)\.\s+(.*?)(?=\n|$)/gm, '<li class="summary-numbered"><span class="number">$1.</span> $2</li>');
    
    // Wrap bullet points and numbered lists in ul/ol
    let finalText = numberedFormatted
      .replace(/<li class="summary-bullet">/g, '<ul class="summary-list"><li class="summary-bullet">')
      .replace(/<\/li>\n(?!<li class="summary-bullet">)/g, '</li></ul>\n')
      .replace(/<li class="summary-numbered">/g, '<ol class="summary-list"><li class="summary-numbered">')
      .replace(/<\/li>\n(?!<li class="summary-numbered">)/g, '</li></ol>\n');
    
    // Fix any unclosed tags
    if (finalText.includes('<li class="summary-bullet">') && !finalText.includes('</ul>')) {
      finalText += '</ul>';
    }
    if (finalText.includes('<li class="summary-numbered">') && !finalText.includes('</ol>')) {
      finalText += '</ol>';
    }
    
    return finalText;
  };
  
  // ===== MAIN FUNCTIONALITY =====
  /**
   * Handles the main summary generation process
   * 1. Validates that at least one file is uploaded
   * 2. Prepares and sends files to the backend
   * 3. Updates UI state during and after processing
   * 4. Handles errors and successful responses
   */
  const handleGenerateSummary = async () => {
    // Validate that at least one file is uploaded
    if (!mp4File && !pdfFile) {
      setError('Please upload at least one file (MP4 or PDF)');
      return;
    }
    
    // Set UI to loading state
    setLoading(true);
    setError(null);
    setSummary('');
    setProgress(0);

    try {
      // Create form data with the uploaded files
      const formData = new FormData();
      if (mp4File) {
        formData.append('mp4_file', mp4File);
      }
      if (pdfFile) {
        formData.append('pdf_file', pdfFile);
      }

      // Send request to the backend API
      const response = await fetch('http://localhost:8000/generate_summary/', {
        method: 'POST',
        body: formData,
      });

      // Handle HTTP errors
      if (!response.ok) {
        throw new Error(`Server responded with ${response.status}: ${response.statusText}`);
      }

      // Parse the JSON response
      const data = await response.json();
      
      // Handle application errors
      if (data.status === 'error') {
        throw new Error(data.message);
      }
      
      // Set progress to 100% on success
      setProgress(100);
      
      // Slightly delay showing the summary for a smoother transition
      setTimeout(() => {
        // Update the summary state with the generated content
        setSummary(data.summary);
        
        // Scroll to the summary section
        if (summaryRef.current) {
          summaryRef.current.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }
      }, 500);
      
    } catch (error) {
      // Log and display any errors that occur
      console.error('Error generating summary:', error);
      setError(`Failed to generate summary: ${error.message}`);
    } finally {
      // Reset loading state
      setLoading(false);
    }
  };
  
  // ===== UTILITY FUNCTIONS =====
  /**
   * Copies the generated summary to the clipboard
   * Provides visual feedback when the copy is successful
   */
  const handleCopySummary = () => {
    if (!summary) return;
    
    // Create a temporary element to get plain text without HTML
    const tempElement = document.createElement('div');
    tempElement.innerHTML = formatSummary(summary);
    const plainText = tempElement.textContent || tempElement.innerText || summary;
    
    // Copy to clipboard and show feedback
    navigator.clipboard.writeText(plainText).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  };
  
  /**
   * Clears a specific file input (MP4 or PDF)
   * Resets both the file state and the file input element
   */
  const handleClearFile = (type) => {
    if (type === 'mp4') {
      setMp4File(null);
      if (mp4InputRef.current) mp4InputRef.current.value = '';
    } else if (type === 'pdf') {
      setPdfFile(null);
      if (pdfInputRef.current) pdfInputRef.current.value = '';
    }
  };

  // ===== COMPONENT RENDER =====
  return (
    <div className="summary-ai">
      <h1>AI Meeting Summary Tool</h1>
      
      {/* File Upload Section */}
      <div className="file-upload">
        <h2>Upload Files</h2>
        
        {/* MP4 Upload Section */}
        <div 
          className={`upload-section ${dragActive.mp4 ? 'drag-active' : ''}`}
          onDragEnter={(e) => handleDrag(e, 'mp4', true)}
          onDragOver={(e) => handleDrag(e, 'mp4', true)}
          onDragLeave={(e) => handleDrag(e, 'mp4', false)}
          onDrop={(e) => handleDrop(e, 'mp4')}
        >
          <label htmlFor="mp4-upload" className="upload-label">
            <div className="upload-icon">🎥</div>
            <span>Upload Meeting Recording (MP4)</span>
            <input
              id="mp4-upload"
              type="file"
              accept=".mp4,video/mp4"
              onChange={handleMp4FileChange}
              ref={mp4InputRef}
            />
          </label>
          {/* Show file info if an MP4 is selected */}
          {mp4File && (
            <div className="file-info">
              <span>{mp4File.name}</span>
              <button 
                className="clear-file-btn" 
                onClick={() => handleClearFile('mp4')}
                title="Remove file"
              >
                ✕
              </button>
            </div>
          )}
        </div>

        {/* PDF Upload Section */}
        <div 
          className={`upload-section ${dragActive.pdf ? 'drag-active' : ''}`}
          onDragEnter={(e) => handleDrag(e, 'pdf', true)}
          onDragOver={(e) => handleDrag(e, 'pdf', true)}
          onDragLeave={(e) => handleDrag(e, 'pdf', false)}
          onDrop={(e) => handleDrop(e, 'pdf')}
        >
          <label htmlFor="pdf-upload" className="upload-label">
            <div className="upload-icon">📄</div>
            <span>Upload Meeting Slides (PDF)</span>
            <input
              id="pdf-upload"
              type="file"
              accept=".pdf,application/pdf"
              onChange={handlePdfFileChange}
              ref={pdfInputRef}
            />
          </label>
          {/* Show file info if a PDF is selected */}
          {pdfFile && (
            <div className="file-info">
              <span>{pdfFile.name}</span>
              <button 
                className="clear-file-btn" 
                onClick={() => handleClearFile('pdf')}
                title="Remove file"
              >
                ✕
              </button>
            </div>
          )}
        </div>

        {/* Generate Summary Button */}
        <button 
          className="generate-button"
          onClick={handleGenerateSummary}
          disabled={loading || (!mp4File && !pdfFile)}
        >
          {loading ? 'Generating Summary...' : 'Generate Summary'}
        </button>
      </div>

      {/* Error Message Display */}
      {error && (
        <div className="error-message">
          <div className="error-icon">⚠️</div>
          {error}
        </div>
      )}

      {/* Loading Indicator with Progress Bar */}
      {loading && (
        <div className="loading-indicator">
          <p>Generating summary, please wait... This may take several minutes.</p>
          <div className="progress-bar">
            <div 
              className="progress-fill" 
              style={{ width: `${progress}%` }}
            ></div>
          </div>
        </div>
      )}

      {/* Summary Display Section */}
      {summary && (
        <div className="summary-section" ref={summaryRef}>
          <div className="summary-header">
            <h2>Meeting Summary</h2>
            <button 
              className={`copy-btn ${copied ? 'copied' : ''}`}
              onClick={handleCopySummary}
              title="Copy to clipboard"
            >
              {copied ? 'Copied! ✓' : 'Copy 📋'}
            </button>
          </div>
          {/* Display formatted summary using dangerouslySetInnerHTML */}
          <div 
            className="summary-content"
            dangerouslySetInnerHTML={{ __html: formatSummary(summary) }}
          />
        </div>
      )}
    </div>
  );
}

export default SummaryAI;
