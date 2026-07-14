import { useState } from 'react';
import { 
  UploadCloud, 
  FileText, 
  CheckCircle2, 
  AlertCircle, 
  Loader2, 
  Sparkles,
  ChevronRight 
} from 'lucide-react';
import api from '../services/api';

/**
 * Upload Page Component.
 * Implements a premium PDF file uploader with status animations,
 * extraction/chunk/embedding metadata outputs, and cache saves.
 */
function Upload() {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [successData, setSuccessData] = useState(null);
  const [error, setError] = useState(null);

  // File drag-over handlers
  const handleDragOver = (e) => e.preventDefault();
  
  const handleDrop = (e) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const droppedFile = e.dataTransfer.files[0];
      if (droppedFile.type === 'application/pdf') {
        setFile(droppedFile);
        setError(null);
        setSuccessData(null);
      } else {
        setError('Only PDF files are allowed.');
      }
    }
  };

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      const selectedFile = e.target.files[0];
      if (selectedFile.type === 'application/pdf') {
        setFile(selectedFile);
        setError(null);
        setSuccessData(null);
      } else {
        setError('Only PDF files are allowed.');
      }
    }
  };

  // Upload handler triggering backend /upload API call
  const handleUpload = async () => {
    if (!file || uploading) return;

    setUploading(true);
    setProgress(15);
    setError(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      setProgress(40);
      
      const response = await api.post('/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        }
      });

      setProgress(85);
      const data = response.data;
      
      // Update success details state
      setSuccessData(data);
      setProgress(100);

      // Save upload event to localStorage cache for dashboard statistics
      const uploadHistory = JSON.parse(localStorage.getItem('docmind_uploads_history') || '[]');
      uploadHistory.unshift({
        filename: data.filename,
        characters: data.characters,
        pages: data.pages,
        chunks: data.chunks,
        timestamp: new Date().toISOString()
      });
      localStorage.setItem('docmind_uploads_history', JSON.stringify(uploadHistory));

      setFile(null);
    } catch (err) {
      console.error(err);
      setError(err.response?.data?.detail || 'An error occurred during file upload or text processing.');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="flex-1 flex flex-col items-center justify-center p-8 bg-slate-950 relative overflow-hidden">
      {/* Decorative glows */}
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-indigo-600/5 rounded-full blur-3xl pointer-events-none"></div>
      <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-cyan-500/5 rounded-full blur-3xl pointer-events-none"></div>

      <div className="w-full max-w-xl relative z-10 space-y-6">
        
        {/* Header Branding */}
        <div className="text-center space-y-2">
          <h1 className="text-3xl font-extrabold bg-gradient-to-r from-white via-slate-200 to-indigo-300 bg-clip-text text-transparent">
            Upload PDF Document
          </h1>
          <p className="text-slate-400 text-sm">
            Add a PDF to automatically extract text, parse chunks, generate embeddings, and index into ChromaDB.
          </p>
        </div>

        {/* Drag & Drop Card Container */}
        <div className="glass-panel border border-white/5 rounded-3xl p-8 shadow-2xl relative">
          
          {/* Main dropzone view */}
          {!successData && !uploading && (
            <div 
              onDragOver={handleDragOver}
              onDrop={handleDrop}
              className="border border-dashed border-white/10 hover:border-indigo-500/40 rounded-2xl p-10 flex flex-col items-center justify-center cursor-pointer transition-all duration-300 bg-slate-950/20"
            >
              <input 
                type="file" 
                id="fileUpload" 
                accept="application/pdf"
                className="hidden" 
                onChange={handleFileChange}
              />
              <label htmlFor="fileUpload" className="flex flex-col items-center cursor-pointer space-y-4">
                <div className="w-14 h-14 rounded-2xl bg-indigo-500/10 flex items-center justify-center border border-indigo-500/20 shadow-md">
                  <UploadCloud className="w-6 h-6 text-indigo-400" />
                </div>
                <div className="text-center">
                  <p className="text-sm font-semibold text-slate-200">Drag and drop file here</p>
                  <p className="text-xs text-slate-500 mt-1">or click to browse from files</p>
                </div>
                <span className="text-[10px] text-indigo-400/70 font-semibold uppercase tracking-wider bg-indigo-500/5 px-2 py-0.5 rounded border border-indigo-500/10">
                  PDF Format Only
                </span>
              </label>
            </div>
          )}

          {/* Selected File Overview */}
          {file && !uploading && (
            <div className="mt-4 p-4 rounded-2xl bg-slate-900 border border-white/5 flex items-center justify-between">
              <div className="flex items-center space-x-3 min-w-0">
                <div className="p-2.5 bg-rose-500/10 rounded-lg text-rose-400 border border-rose-500/10 shrink-0">
                  <FileText className="w-5 h-5" />
                </div>
                <div className="min-w-0">
                  <p className="text-sm font-medium text-slate-200 truncate">{file.name}</p>
                  <p className="text-[10px] text-slate-500">{(file.size / (1024 * 1024)).toFixed(2)} MB</p>
                </div>
              </div>
              <button 
                onClick={handleUpload}
                className="px-4 py-2 bg-indigo-500 hover:bg-indigo-600 text-white text-xs font-semibold rounded-xl shadow-lg shadow-indigo-500/20 transition-all duration-200 flex items-center space-x-1"
              >
                <span>Process File</span>
                <ChevronRight className="w-3.5 h-3.5" />
              </button>
            </div>
          )}

          {/* Progress / Pipeline Status View */}
          {uploading && (
            <div className="space-y-6 py-6">
              <div className="flex flex-col items-center justify-center space-y-4">
                <Loader2 className="w-10 h-10 animate-spin text-indigo-400" />
                <div className="text-center space-y-1">
                  <h3 className="text-sm font-semibold text-slate-200">
                    {progress < 40 ? 'Saving file locally...' : progress < 85 ? 'Extracting and chunking text...' : 'Generating embeddings & indexing vectors...'}
                  </h3>
                  <p className="text-xs text-slate-500">Please do not refresh the page.</p>
                </div>
              </div>

              {/* Progress bar container */}
              <div className="w-full bg-slate-900 rounded-full h-2 overflow-hidden border border-white/5">
                <div 
                  className="bg-indigo-500 h-full rounded-full transition-all duration-300"
                  style={{ width: `${progress}%` }}
                ></div>
              </div>
            </div>
          )}

          {/* Success Response View */}
          {successData && (
            <div className="space-y-6 text-center py-4">
              <div className="flex flex-col items-center space-y-3">
                <CheckCircle2 className="w-14 h-14 text-emerald-400" />
                <h3 className="text-lg font-bold text-white">Indexing Completed!</h3>
                <p className="text-xs text-slate-400 truncate max-w-[80%]">{successData.filename}</p>
              </div>

              {/* Metadata Cards Grid */}
              <div className="grid grid-cols-3 gap-3">
                <div className="bg-slate-900 border border-white/5 rounded-xl p-3.5 text-center">
                  <span className="text-[10px] text-slate-500 font-semibold tracking-wide uppercase">Pages</span>
                  <p className="text-lg font-bold text-white mt-1">{successData.pages}</p>
                </div>
                <div className="bg-slate-900 border border-white/5 rounded-xl p-3.5 text-center">
                  <span className="text-[10px] text-slate-500 font-semibold tracking-wide uppercase">Characters</span>
                  <p className="text-lg font-bold text-white mt-1">{successData.characters}</p>
                </div>
                <div className="bg-slate-900 border border-white/5 rounded-xl p-3.5 text-center">
                  <span className="text-[10px] text-slate-500 font-semibold tracking-wide uppercase">Chunks</span>
                  <p className="text-lg font-bold text-indigo-400 mt-1">{successData.chunks}</p>
                </div>
              </div>

              <button 
                onClick={() => setSuccessData(null)}
                className="w-full py-3 bg-slate-900 hover:bg-slate-800 text-xs font-semibold text-slate-300 hover:text-white rounded-xl border border-white/5 hover:border-white/10 transition-all duration-200"
              >
                Upload another document
              </button>
            </div>
          )}

          {/* Error Message Display */}
          {error && (
            <div className="mt-4 p-4 bg-rose-500/10 border border-rose-500/20 rounded-2xl flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-rose-400 shrink-0 mt-0.5" />
              <div className="text-xs text-rose-400 leading-normal flex-1">
                <span className="font-semibold block mb-1">Processing Error</span>
                {error}
              </div>
            </div>
          )}

        </div>

      </div>
    </div>
  );
}

export default Upload;
