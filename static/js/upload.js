/**
 * Upload Page JavaScript
 * Handles drag-and-drop, file selection, validation, and upload flow
 */

const dropZone = document.getElementById('dropZone');
const fileInput = document.getElementById('fileInput');
const filePreview = document.getElementById('filePreview');
const fileName = document.getElementById('fileName');
const fileSize = document.getElementById('fileSize');
const removeFile = document.getElementById('removeFile');
const uploadBtn = document.getElementById('uploadBtn');
const uploadProgress = document.getElementById('uploadProgress');
const progressBar = document.getElementById('progressBar');
const progressLabel = document.getElementById('progressLabel');
const progressPct = document.getElementById('progressPct');
const uploadError = document.getElementById('uploadError');
const errorMsg = document.getElementById('errorMsg');

let selectedFile = null;

// ── Drag & Drop ──────────────────────────────────────────────────

dropZone.addEventListener('dragover', (e) => {
  e.preventDefault();
  dropZone.classList.add('dragover');
});

dropZone.addEventListener('dragleave', () => {
  dropZone.classList.remove('dragover');
});

dropZone.addEventListener('drop', (e) => {
  e.preventDefault();
  dropZone.classList.remove('dragover');
  const files = e.dataTransfer.files;
  if (files.length > 0) handleFileSelected(files[0]);
});

// Click on drop zone (not label) to open file browser
dropZone.addEventListener('click', (e) => {
  if (e.target.tagName !== 'LABEL' && e.target.tagName !== 'INPUT') {
    fileInput.click();
  }
});

fileInput.addEventListener('change', () => {
  if (fileInput.files.length > 0) handleFileSelected(fileInput.files[0]);
});

removeFile.addEventListener('click', resetFile);

// ── File Handling ────────────────────────────────────────────────

function handleFileSelected(file) {
  hideError();

  if (!file.name.toLowerCase().endsWith('.pdf')) {
    showError('Only PDF files are supported. Please select a valid PDF.');
    return;
  }

  const maxMB = 50;
  if (file.size > maxMB * 1024 * 1024) {
    showError(`File is too large (${(file.size / 1024 / 1024).toFixed(1)} MB). Maximum size is ${maxMB} MB.`);
    return;
  }

  selectedFile = file;
  const sizeMB = (file.size / 1024 / 1024).toFixed(2);

  fileName.textContent = file.name;
  fileSize.textContent = `${sizeMB} MB`;

  filePreview.classList.remove('d-none');
  dropZone.classList.add('d-none');

  uploadBtn.classList.remove('disabled');
  uploadBtn.disabled = false;
}

function resetFile() {
  selectedFile = null;
  fileInput.value = '';
  filePreview.classList.add('d-none');
  dropZone.classList.remove('d-none');
  uploadBtn.classList.add('disabled');
  uploadBtn.disabled = true;
  hideError();
}

// ── Upload Flow ──────────────────────────────────────────────────

uploadBtn.addEventListener('click', startUpload);

async function startUpload() {
  if (!selectedFile) return;

  uploadBtn.disabled = true;
  hideError();

  uploadProgress.classList.remove('d-none');
  filePreview.classList.add('d-none');

  const steps = [
    { label: 'Uploading & validating PDF...', pct: 15 },
    { label: 'Extracting text from pages...', pct: 35 },
    { label: 'Splitting document into chunks...', pct: 55 },
    { label: 'Generating embeddings...', pct: 75 },
    { label: 'Indexing in FAISS vector store...', pct: 90 },
    { label: 'Finalizing...', pct: 98 },
  ];

  // Animate steps while uploading
  let stepIndex = 0;
  const stepInterval = setInterval(() => {
    if (stepIndex < steps.length) {
      const step = steps[stepIndex];
      progressLabel.textContent = step.label;
      progressPct.textContent = step.pct + '%';
      progressBar.style.width = step.pct + '%';
      stepIndex++;
    }
  }, 1500);

  const formData = new FormData();
  formData.append('file', selectedFile);

  try {
    const response = await fetch('/api/upload', {
      method: 'POST',
      body: formData,
    });

    clearInterval(stepInterval);
    const data = await response.json();

    if (data.success) {
      // Complete progress
      progressBar.style.width = '100%';
      progressPct.textContent = '100%';
      progressLabel.textContent = 'Processing complete!';
      progressBar.classList.remove('progress-bar-animated');
      progressBar.classList.add('bg-success');

      // Store session info
      sessionStorage.setItem('session_id', data.session_id);
      sessionStorage.setItem('doc_metadata', JSON.stringify(data.metadata));

      setTimeout(() => {
        window.location.href = '/dashboard';
      }, 1000);

    } else {
      clearInterval(stepInterval);
      uploadProgress.classList.add('d-none');
      filePreview.classList.remove('d-none');
      uploadBtn.disabled = false;
      showError(data.error || 'Upload failed. Please try again.');
    }

  } catch (err) {
    clearInterval(stepInterval);
    uploadProgress.classList.add('d-none');
    filePreview.classList.remove('d-none');
    uploadBtn.disabled = false;
    showError('Network error. Please check your connection and try again.');
    console.error('Upload error:', err);
  }
}

// ── Helpers ──────────────────────────────────────────────────────

function showError(msg) {
  errorMsg.textContent = msg;
  uploadError.classList.remove('d-none');
}

function hideError() {
  uploadError.classList.add('d-none');
}
