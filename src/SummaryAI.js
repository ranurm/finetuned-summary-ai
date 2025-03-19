import React, { useState, useRef, useEffect } from 'react';
import './SummaryAI.css';

function SummaryAI() {
  const [mp4File, setMp4File] = useState(null);
  const [pdfFile, setPdfFile] = useState(null);
  const [summary, setSummary] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [copied, setCopied] = useState(false);
  const [dragActive, setDragActive] = useState({ mp4: false, pdf: false });
  const [progress, setProgress] = useState(0);
  
  const mp4InputRef = useRef(null);
  const pdfInputRef = useRef(null);
  const summaryRef = useRef(null);
  
  // Progress animation during loading
  useEffect(() => {
    let interval;
    if (loading) {
      interval = setInterval(() => {
        setProgress((prev) => {
          // Slowly increase progress to 90% (the real progress is unknown)
          if (prev < 90) {
            return prev + (90 - prev) * 0.05;
          }
          return prev;
        });
      }, 500);
    } else {
      setProgress(0);
    }
    
    return () => clearInterval(interval);
  }, [loading]);
  
  // Handle file change
  const handleMp4FileChange = (e) => {
    const file = e.target.files?.[0];
    if (file && file.type === 'video/mp4') {
      setMp4File(file);
      setError(null);
    } else if (file) {
      setError('Please select a valid MP4 file');
    }
  };

  const handlePdfFileChange = (e) => {
    const file = e.target.files?.[0];
    if (file && file.type === 'application/pdf') {
      setPdfFile(file);
      setError(null);
    } else if (file) {
      setError('Please select a valid PDF file');
    }
  };
  
  // Handle drag events
  const handleDrag = (e, type, active) => {
    e.preventDefault();
    e.stopPropagation();
    
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive({ ...dragActive, [type]: true });
    } else if (e.type === 'dragleave') {
      setDragActive({ ...dragActive, [type]: false });
    }
  };
  
  // Handle drop event
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
  
  // Format summary text with enhanced headlines and bullet points
  const formatSummary = (text) => {
    if (!text) return '';
    
    // Replace **Headline** with styled headline
    const headlineFormatted = text.replace(/\*\*(.*?)\*\*/g, '<h3 class="summary-headline">$1</h3>');
    
    // Enhance bullet points and numbered lists
    const bulletFormatted = headlineFormatted.replace(/- (.*?)(?=\n|$)/g, '<li class="summary-bullet">$1</li>');
    const numberedFormatted = bulletFormatted.replace(/(\d+)\. (.*?)(?=\n|$)/g, '<li class="summary-numbered"><span class="number">$1.</span> $2</li>');
    
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
  
  // Generate summary
  const handleGenerateSummary = async () => {
    if (!mp4File && !pdfFile) {
      setError('Please upload at least one file (MP4 or PDF)');
      return;
    }
    
    setLoading(true);
    setError(null);
    setSummary('');
    setProgress(0);

    try {
      const formData = new FormData();
      if (mp4File) {
        formData.append('mp4_file', mp4File);
      }
      if (pdfFile) {
        formData.append('pdf_file', pdfFile);
      }

      const response = await fetch('http://localhost:8000/generate_summary/', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`Server responded with ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      
      if (data.status === 'error') {
        throw new Error(data.message);
      }
      
      // Set progress to 100% on success
      setProgress(100);
      
      // Slightly delay showing the summary for a smoother transition
      setTimeout(() => {
        setSummary(data.summary);
        
        // Scroll to the summary
        if (summaryRef.current) {
          summaryRef.current.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }
      }, 500);
      
    } catch (error) {
      console.error('Error generating summary:', error);
      setError(`Failed to generate summary: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };
  
  // Copy summary to clipboard
  const handleCopySummary = () => {
    if (!summary) return;
    
    // Create a temporary element to get plain text without HTML
    const tempElement = document.createElement('div');
    tempElement.innerHTML = formatSummary(summary);
    const plainText = tempElement.textContent || tempElement.innerText || summary;
    
    navigator.clipboard.writeText(plainText).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  };
  
  // Clear a specific file
  const handleClearFile = (type) => {
    if (type === 'mp4') {
      setMp4File(null);
      if (mp4InputRef.current) mp4InputRef.current.value = '';
    } else if (type === 'pdf') {
      setPdfFile(null);
      if (pdfInputRef.current) pdfInputRef.current.value = '';
    }
  };

  return (
    <div className="summary-ai">
      <h1>AI Meeting Summary Tool</h1>
      
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

        <button 
          className="generate-button"
          onClick={handleGenerateSummary}
          disabled={loading || (!mp4File && !pdfFile)}
        >
          {loading ? 'Generating Summary...' : 'Generate Summary'}
        </button>
      </div>

      {error && (
        <div className="error-message">
          <div className="error-icon">⚠️</div>
          {error}
        </div>
      )}

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
