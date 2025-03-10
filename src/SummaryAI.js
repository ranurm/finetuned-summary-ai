import React, { useState, useRef } from 'react';
import './SummaryAI.css';

const SummaryAI = () => {
  const [mp4File, setMp4File] = useState(null);
  const [pdfFile, setPdfFile] = useState(null);

  const mp4InputRef = useRef(null);
  const pdfInputRef = useRef(null);

  const handleFileDrop = (e, type) => {
    e.preventDefault();
    const file = e.dataTransfer.files[0];
    if (type === 'mp4' && file.type === 'video/mp4') {
      setMp4File(file);
    } else if (type === 'pdf' && file.type === 'application/pdf') {
      setPdfFile(file);
    } else {
      alert(`Please upload a valid ${type.toUpperCase()} file.`);
    }
  };

  const handleFileChange = (e, type) => {
    const file = e.target.files[0];
    if (type === 'mp4' && file?.type === 'video/mp4') {
      setMp4File(file);
    } else if (type === 'pdf' && file?.type === 'application/pdf') {
      setPdfFile(file);
    } else {
      alert(`Please select a valid ${type.toUpperCase()} file.`);
    }
  };

  const preventDefaults = (e) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const isValid = () => {
    const mp4Valid = mp4File && mp4File.type === 'video/mp4';
    const pdfValid = pdfFile && pdfFile.type === 'application/pdf';
    return mp4Valid || pdfValid;
  };

  return (
    <div className="summary-ai">
      <h2>AI Meeting Summary Tool</h2>
      <p className="instruction-text">
        Upload your meeting recording and slides.<br />
        We'll generate a smart summary for you.
      </p>

      {/* MP4 Upload Box */}
      <div
        className="upload-box"
        onDrop={(e) => handleFileDrop(e, 'mp4')}
        onDragOver={preventDefaults}
        onDragEnter={preventDefaults}
        onDragLeave={preventDefaults}
      >
        <p>🎥 Drag & drop your MP4 meeting recording here</p>
        <button className="upload-btn" onClick={() => mp4InputRef.current.click()}>
          Choose MP4 File
        </button>
        <input
          type="file"
          accept="video/mp4"
          ref={mp4InputRef}
          onChange={(e) => handleFileChange(e, 'mp4')}
          style={{ display: 'none' }}
        />
        {mp4File && <p className="file-name">Selected: {mp4File.name}</p>}
      </div>

      {/* PDF Upload Box */}
      <div
        className="upload-box"
        onDrop={(e) => handleFileDrop(e, 'pdf')}
        onDragOver={preventDefaults}
        onDragEnter={preventDefaults}
        onDragLeave={preventDefaults}
      >
        <p>📄 Drag & drop your PDF meeting slides here</p>
        <button className="upload-btn" onClick={() => pdfInputRef.current.click()}>
          Choose PDF File
        </button>
        <input
          type="file"
          accept="application/pdf"
          ref={pdfInputRef}
          onChange={(e) => handleFileChange(e, 'pdf')}
          style={{ display: 'none' }}
        />
        {pdfFile && <p className="file-name">Selected: {pdfFile.name}</p>}
      </div>

      {/* Proceed Button */}
      <button
        className={`proceed-btn ${isValid() ? 'valid' : 'invalid'}`}
        disabled={!isValid()}
      >
        {isValid() ? 'Generate Summary' : 'Please upload a valid MP4 or PDF'}
      </button>
    </div>
  );
};

export default SummaryAI;
