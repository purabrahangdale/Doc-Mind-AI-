import { useState, useEffect, useRef } from 'react';
import ReactMarkdown from 'react-markdown';
import { 
  Send, 
  Trash2, 
  Copy, 
  Check, 
  Bot, 
  User, 
  Loader2, 
  FileText, 
  Sparkles,
  Plus,
  Mic,
  MicOff,
  Image,
  FileCode,
  X,
  AlertCircle
} from 'lucide-react';
import { sendMessage } from '../services/chatApi';
import api from '../services/api';

/**
 * Chat page component implementing a ChatGPT-style RAG conversational UI.
 * Integrates direct file uploader and microphone voice input inside the composer.
 */
function Chat() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [copiedId, setCopiedId] = useState(null);
  const [error, setError] = useState(null);
  
  // Attachments & Dropdown Popover States
  const [attachments, setAttachments] = useState([]);
  const [isAttachmentMenuOpen, setIsAttachmentMenuOpen] = useState(false);

  // Microphone Transcription States
  const [isRecording, setIsRecording] = useState(false);
  const [isInitializing, setIsInitializing] = useState(false);
  const [recordingStatus, setRecordingStatus] = useState('Ready');

  const messagesEndRef = useRef(null);
  const dropdownRef = useRef(null);
  const recognitionRef = useRef(null);
  const textareaRef = useRef(null);
  const preRecordingInputRef = useRef('');
  const silenceTimeoutRef = useRef(null);

  // File Input References
  const pdfInputRef = useRef(null);
  const docInputRef = useRef(null);
  const imgInputRef = useRef(null);

  // Load chat session from local storage on mount
  useEffect(() => {
    const cachedSession = localStorage.getItem('docmind_current_chat');
    if (cachedSession) {
      setMessages(JSON.parse(cachedSession));
    } else {
      setMessages([
        {
          id: 'welcome',
          role: 'assistant',
          text: 'Hello! I am DocMind AI. Upload a document using the `+` button and ask me anything about it.',
          timestamp: new Date().toISOString(),
          sources: []
        }
      ]);
    }
  }, []);

  // Helper to reset the silence auto-stop timeout (2.5 seconds of silence)
  const resetSilenceTimeout = () => {
    if (silenceTimeoutRef.current) {
      clearTimeout(silenceTimeoutRef.current);
    }
    silenceTimeoutRef.current = setTimeout(() => {
      if (recognitionRef.current) {
        recognitionRef.current.stop();
      }
    }, 2500);
  };

  // Initialize Speech Recognition
  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
      const rec = new SpeechRecognition();
      rec.continuous = true;
      rec.interimResults = true;
      rec.lang = 'en-US';

      rec.onstart = () => {
        setIsInitializing(false);
        setIsRecording(true);
        setRecordingStatus('Listening...');
        resetSilenceTimeout();
      };

      rec.onspeechstart = () => {
        resetSilenceTimeout();
        setRecordingStatus('Listening...');
      };

      rec.onspeechend = () => {
        // Speech ended event from API, silence detection will follow if no new speech is heard
        console.log('Speech ended, waiting for silence timeout or further speech.');
      };

      rec.onresult = (event) => {
        resetSilenceTimeout();
        setRecordingStatus('Listening...');
        
        let sessionTranscript = '';
        for (let i = 0; i < event.results.length; ++i) {
          sessionTranscript += event.results[i][0].transcript;
        }

        const prefix = preRecordingInputRef.current;
        setInput(prefix + (prefix && sessionTranscript ? ' ' : '') + sessionTranscript);
      };

      rec.onerror = (event) => {
        console.error('Speech recognition error:', event.error);
        setIsInitializing(false);
        setIsRecording(false);
        setRecordingStatus('Ready');
        
        if (silenceTimeoutRef.current) {
          clearTimeout(silenceTimeoutRef.current);
        }

        if (event.error === 'not-allowed') {
          setError('Microphone permission was denied.');
        } else if (event.error === 'no-speech') {
          console.log('No speech detected.');
        } else {
          setError(`Voice input error: ${event.error}`);
        }
      };

      rec.onend = () => {
        setIsInitializing(false);
        setIsRecording(false);
        setRecordingStatus('Ready');
        if (silenceTimeoutRef.current) {
          clearTimeout(silenceTimeoutRef.current);
        }
      };

      recognitionRef.current = rec;
    }

    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.abort();
      }
      if (silenceTimeoutRef.current) {
        clearTimeout(silenceTimeoutRef.current);
      }
    };
  }, []);

  // Dropdown click outside listener
  useEffect(() => {
    function handleClickOutside(e) {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target)) {
        setIsAttachmentMenuOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Auto-expand textarea based on text length
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
    }
  }, [input]);

  // Save current conversation session to local storage
  const saveSession = (newMessages) => {
    setMessages(newMessages);
    localStorage.setItem('docmind_current_chat', JSON.stringify(newMessages));
  };

  // Auto-scroll to the bottom of the conversation
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  // Handle message submission
  const handleSend = async (e) => {
    e?.preventDefault();
    if (!input.trim() || loading) return;

    const userQuery = input.trim();
    setInput('');
    setError(null);

    // Context validation check: If no documents exist in local storage uploads history
    // and no attachments exist in the current composer session, show a friendly warning.
    const uploadsHistory = JSON.parse(localStorage.getItem('docmind_uploads_history') || '[]');
    if (uploadsHistory.length === 0 && attachments.length === 0) {
      const welcomeMsgId = Date.now().toString();
      const finalMessages = [
        ...messages,
        {
          id: welcomeMsgId,
          role: 'user',
          text: userQuery,
          timestamp: new Date().toISOString()
        },
        {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          text: "Please upload a document to start asking questions about it.",
          timestamp: new Date().toISOString(),
          sources: []
        }
      ];
      saveSession(finalMessages);
      return;
    }

    const userMsgId = Date.now().toString();
    const assistantMsgId = (Date.now() + 1).toString();

    const updatedMessages = [
      ...messages,
      {
        id: userMsgId,
        role: 'user',
        text: userQuery,
        timestamp: new Date().toISOString()
      }
    ];

    saveSession(updatedMessages);
    setLoading(true);

    try {
      // Call backend chat API, passing document_id filter if an attachment is present
      const docId = attachments.length > 0 ? attachments[attachments.length - 1].document_id : null;
      const response = await sendMessage(userQuery, docId);
      
      const newAssistantMsg = {
        id: assistantMsgId,
        role: 'assistant',
        text: response.answer,
        timestamp: new Date().toISOString(),
        sources: response.sources || []
      };

      const finalMessages = [...updatedMessages, newAssistantMsg];
      saveSession(finalMessages);

      // Append to query history
      const historyItems = JSON.parse(localStorage.getItem('docmind_query_history') || '[]');
      historyItems.unshift({
        id: assistantMsgId,
        question: userQuery,
        answer: response.answer,
        timestamp: new Date().toISOString(),
        sources: response.sources || []
      });
      localStorage.setItem('docmind_query_history', JSON.stringify(historyItems));

    } catch (err) {
      console.error(err);
      setError(err.response?.data?.detail || 'Failed to generate answer. Make sure your local services are running.');
    } finally {
      setLoading(false);
    }
  };

  // Microphone toggle function
  const toggleRecording = () => {
    if (isRecording || isInitializing) {
      recognitionRef.current?.stop();
    } else {
      if (!recognitionRef.current) {
        setError('Speech recognition is not supported in this browser. Try Chrome or Edge.');
        return;
      }
      setError(null);
      setIsInitializing(true);
      setRecordingStatus('Initializing...');
      preRecordingInputRef.current = input;
      try {
        recognitionRef.current.start();
      } catch (err) {
        console.error(err);
        setIsInitializing(false);
        setRecordingStatus('Ready');
      }
    }
  };

  // Immediate file upload indexing pipeline call
  const handleFileUpload = async (e, type) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setIsAttachmentMenuOpen(false);
    setError(null);
    
    const id = Date.now().toString();
    const newAttachment = {
      id,
      name: file.name,
      size: (file.size / (1024 * 1024)).toFixed(2) + ' MB',
      progress: 15,
      status: 'Uploading...',
      type
    };

    setAttachments((prev) => [...prev, newAttachment]);

    const formData = new FormData();
    formData.append('file', file);

    // Simulated progress incrementer for visual status changes
    let progressVal = 15;
    const progressInterval = setInterval(() => {
      progressVal = Math.min(progressVal + 15, 85);
      let statusText = 'Uploading...';
      if (progressVal >= 40 && progressVal < 70) statusText = 'Processing document...';
      if (progressVal >= 70) statusText = 'Creating embeddings...';

      setAttachments((prev) => 
        prev.map((att) => 
          att.id === id ? { ...att, progress: progressVal, status: statusText } : att
        )
      );
    }, 450);

    try {
      const response = await api.post('/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        }
      });

      clearInterval(progressInterval);
      const data = response.data;

      // Save upload event to localStorage cache for dashboard statistics
      const uploadHistory = JSON.parse(localStorage.getItem('docmind_uploads_history') || '[]');
      uploadHistory.unshift({
        filename: data.filename,
        characters: data.characters,
        pages: data.pages,
        chunks: data.chunks,
        document_id: data.document_id,
        timestamp: new Date().toISOString()
      });
      localStorage.setItem('docmind_uploads_history', JSON.stringify(uploadHistory));

      setAttachments((prev) => 
        prev.map((att) => 
          att.id === id ? { ...att, progress: 100, status: 'Ready to chat ✅', document_id: data.document_id } : att
        )
      );

    } catch (err) {
      clearInterval(progressInterval);
      setAttachments((prev) => prev.filter((att) => att.id !== id));
      setError(err.response?.data?.detail || `Failed to process ${file.name}. Verify the backend services.`);
    }

    // Reset file input value so same file can be selected again
    e.target.value = '';
  };

  const removeAttachment = (id) => {
    setAttachments((prev) => prev.filter((att) => att.id !== id));
  };

  // Keyboard handlers
  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleCopy = (text, id) => {
    navigator.clipboard.writeText(text).then(() => {
      setCopiedId(id);
      setTimeout(() => setCopiedId(null), 2000);
    });
  };

  const handleClearChat = () => {
    if (window.confirm('Are you sure you want to clear this conversation?')) {
      const resetMessages = [
        {
          id: 'welcome',
          role: 'assistant',
          text: 'Hello! I am DocMind AI. Upload a document using the `+` button and ask me anything about it.',
          timestamp: new Date().toISOString(),
          sources: []
        }
      ];
      setMessages(resetMessages);
      setAttachments([]);
      localStorage.removeItem('docmind_current_chat');
      setError(null);
    }
  };

  return (
    <div className="flex-1 flex flex-col h-screen overflow-hidden bg-slate-950 relative">
      {/* Background decorations */}
      <div className="absolute top-1/4 left-1/3 w-96 h-96 bg-indigo-600/5 rounded-full blur-3xl pointer-events-none"></div>
      <div className="absolute bottom-1/4 right-1/3 w-96 h-96 bg-cyan-500/5 rounded-full blur-3xl pointer-events-none"></div>

      {/* Top Header */}
      <header className="h-16 glass-panel border-b border-white/5 flex items-center justify-between px-8 relative z-10 shrink-0">
        <div className="flex items-center space-x-3">
          <div className="w-8 h-8 rounded-lg bg-indigo-500/10 flex items-center justify-center border border-indigo-500/20">
            <Bot className="w-4 h-4 text-indigo-400" />
          </div>
          <div>
            <h1 className="font-semibold text-white text-sm">Interactive RAG Chat</h1>
            <p className="text-[10px] text-slate-400">Unified Document Assistant</p>
          </div>
        </div>

        <button 
          onClick={handleClearChat}
          className="flex items-center space-x-2 text-xs text-slate-400 hover:text-rose-400 px-3 py-1.5 rounded-lg hover:bg-rose-500/5 border border-transparent hover:border-rose-500/10 transition-all duration-200"
          title="Clear Conversation"
        >
          <Trash2 className="w-3.5 h-3.5" />
          <span>Clear Chat</span>
        </button>
      </header>

      {/* Messages scroll section */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6 scrollbar-thin">
        <div className="max-w-3xl mx-auto space-y-6">
          {messages.map((msg) => (
            <div 
              key={msg.id} 
              className={`flex items-start gap-4 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}
            >
              <div className={`w-8 h-8 rounded-lg flex items-center justify-center shrink-0 border shadow-sm ${
                msg.role === 'user' 
                  ? 'bg-gradient-to-tr from-cyan-500 to-indigo-500 text-white border-cyan-400/20' 
                  : 'bg-slate-900 border-white/5 text-indigo-400'
              }`}>
                {msg.role === 'user' ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
              </div>

              <div className="max-w-[80%] flex flex-col space-y-2">
                <div className={`rounded-2xl px-5 py-3.5 text-sm leading-relaxed border ${
                  msg.role === 'user' 
                    ? 'bg-indigo-600/10 border-indigo-500/20 text-slate-100 rounded-tr-none' 
                    : 'bg-slate-900/55 border-white/5 text-slate-200 rounded-tl-none'
                }`}>
                  {msg.role === 'assistant' ? (
                    <div className="prose prose-invert prose-sm break-words">
                      <ReactMarkdown>
                        {msg.text}
                      </ReactMarkdown>
                    </div>
                  ) : (
                    <p className="whitespace-pre-wrap">{msg.text}</p>
                  )}
                </div>

                <div className={`flex items-center gap-3 text-[10px] text-slate-500 ${msg.role === 'user' ? 'justify-end' : ''}`}>
                  <span>{new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                  {msg.role === 'assistant' && msg.id !== 'welcome' && (
                    <button 
                      onClick={() => handleCopy(msg.text, msg.id)}
                      className="flex items-center gap-1 hover:text-white transition-colors"
                    >
                      {copiedId === msg.id ? (
                        <>
                          <Check className="w-3 h-3 text-emerald-400" />
                          <span className="text-emerald-400">Copied</span>
                        </>
                      ) : (
                        <>
                          <Copy className="w-3 h-3" />
                          <span>Copy</span>
                        </>
                      )}
                    </button>
                  )}
                </div>

                {msg.role === 'assistant' && msg.sources && msg.sources.length > 0 && (
                  <div className="pt-2 border-t border-white/5 mt-2 space-y-1.5">
                    <span className="text-[10px] text-indigo-400 font-semibold uppercase tracking-wider block">Sources Used:</span>
                    <div className="flex flex-wrap gap-2">
                      {msg.sources.map((src, index) => (
                        <div 
                          key={index}
                          className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md bg-slate-900 border border-white/5 text-[11px] text-slate-300"
                        >
                          <FileText className="w-3 h-3 text-indigo-400 shrink-0" />
                          <span className="truncate max-w-[150px]">{src.source || 'Document'}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          ))}

          {loading && (
            <div className="flex items-start gap-4">
              <div className="w-8 h-8 rounded-lg bg-slate-900 border border-white/5 text-indigo-400 flex items-center justify-center shrink-0">
                <Bot className="w-4 h-4" />
              </div>
              <div className="bg-slate-900/55 border border-white/5 rounded-2xl rounded-tl-none px-5 py-3.5 text-sm text-slate-400 flex items-center gap-3">
                <Loader2 className="w-4 h-4 animate-spin text-indigo-400" />
                <span>DocMind AI is reading document context...</span>
              </div>
            </div>
          )}

          {error && (
            <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-sm text-rose-400 flex items-start gap-3 max-w-3xl mx-auto">
              <AlertCircle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
              <div className="flex-1">{error}</div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Hidden File Input Nodes */}
      <input 
        type="file" 
        ref={pdfInputRef} 
        accept="application/pdf" 
        onChange={(e) => handleFileUpload(e, 'pdf')}
        className="hidden" 
      />
      <input 
        type="file" 
        ref={docInputRef} 
        accept=".doc,.docx" 
        onChange={(e) => handleFileUpload(e, 'doc')}
        className="hidden" 
      />
      <input 
        type="file" 
        ref={imgInputRef} 
        accept="image/*" 
        onChange={(e) => handleFileUpload(e, 'image')}
        className="hidden" 
      />

      {/* Unified Input Footer Area */}
      <footer className="p-6 shrink-0 relative z-10 max-w-3xl w-full mx-auto space-y-4">
        {/* Attached Files Preview Grid */}
        {attachments.length > 0 && (
          <div className="flex flex-wrap gap-3 p-3 bg-slate-900/50 border border-white/5 rounded-2xl">
            {attachments.map((att) => (
              <div 
                key={att.id}
                className="flex items-center gap-3 bg-slate-950 border border-white/5 rounded-xl p-3 text-xs text-slate-300 min-w-[200px] max-w-[280px] relative overflow-hidden shadow-md"
              >
                {/* Progress bar background overlay */}
                <div 
                  className="absolute bottom-0 left-0 bg-indigo-500/10 h-1 transition-all duration-300"
                  style={{ width: `${att.progress}%` }}
                ></div>

                <div className="p-2 bg-indigo-500/10 rounded-lg text-indigo-400 shrink-0 border border-indigo-500/20">
                  {att.type === 'image' ? <Image className="w-4 h-4" /> : <FileText className="w-4 h-4" />}
                </div>

                <div className="min-w-0 flex-1 space-y-0.5">
                  <p className="font-semibold text-slate-200 truncate pr-4">{att.name}</p>
                  <p className="text-[10px] text-slate-500">{att.size} • {att.status}</p>
                </div>

                <button 
                  onClick={() => removeAttachment(att.id)}
                  className="p-1 rounded hover:bg-white/5 text-slate-500 hover:text-white shrink-0"
                >
                  <X className="w-3.5 h-3.5" />
                </button>
              </div>
            ))}
          </div>
        )}

        {/* Input Bar */}
        <div className="relative flex items-end">
          
          {/* Dropdown Menu Composer */}
          <div className="relative" ref={dropdownRef}>
            <button
              type="button"
              onClick={() => setIsAttachmentMenuOpen(!isAttachmentMenuOpen)}
              className="mb-1.5 p-2.5 rounded-xl bg-slate-900 border border-white/5 text-slate-400 hover:text-white hover:border-white/10 transition-all duration-200 mr-2 flex items-center justify-center shrink-0"
              title="Add attachment"
            >
              <Plus className={`w-4 h-4 transition-transform duration-300 ${isAttachmentMenuOpen ? 'rotate-45 text-indigo-400' : ''}`} />
            </button>

            {isAttachmentMenuOpen && (
              <div className="absolute bottom-14 left-0 w-52 bg-slate-900 border border-white/5 rounded-2xl p-2 shadow-2xl z-50 animate-in fade-in slide-in-from-bottom-2 duration-200">
                <button
                  type="button"
                  onClick={() => pdfInputRef.current?.click()}
                  className="w-full flex items-center space-x-3 px-3 py-2.5 rounded-xl text-left text-xs font-semibold text-slate-300 hover:bg-white/5 hover:text-white transition-colors"
                >
                  <FileText className="w-4 h-4 text-indigo-400" />
                  <span>Upload PDF</span>
                </button>
                <button
                  type="button"
                  onClick={() => docInputRef.current?.click()}
                  className="w-full flex items-center space-x-3 px-3 py-2.5 rounded-xl text-left text-xs font-semibold text-slate-300 hover:bg-white/5 hover:text-white transition-colors"
                >
                  <FileCode className="w-4 h-4 text-cyan-400" />
                  <span>Upload Document (.doc/.docx)</span>
                </button>
                <button
                  type="button"
                  onClick={() => imgInputRef.current?.click()}
                  className="w-full flex items-center space-x-3 px-3 py-2.5 rounded-xl text-left text-xs font-semibold text-slate-300 hover:bg-white/5 hover:text-white transition-colors"
                >
                  <Image className="w-4 h-4 text-emerald-400" />
                  <span>Upload Image (.png/.jpg/.jpeg)</span>
                </button>
              </div>
            )}
          </div>

          {/* Text Area & Voice Input Container */}
          <div className="flex-1 relative flex items-end bg-slate-900 border border-white/5 focus-within:border-indigo-500/40 rounded-2xl shadow-xl transition-all duration-200">
            <textarea
              ref={textareaRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask DocMind AI a question..."
              rows={1}
              disabled={loading}
              className="flex-1 bg-transparent border-0 pl-5 pr-14 py-4 text-sm text-slate-200 placeholder-slate-500 focus:outline-none resize-none min-h-[50px] leading-relaxed max-h-[150px] scrollbar-none"
            />
            
            {/* Microphone Button */}
            <button
              type="button"
              onClick={toggleRecording}
              disabled={loading || isInitializing}
              className={`mb-2.5 p-2 rounded-xl transition-all duration-300 shrink-0 ${
                isRecording 
                  ? 'bg-rose-500 text-white animate-pulse shadow-lg shadow-rose-500/20' 
                  : isInitializing
                    ? 'bg-amber-500/20 text-amber-400 cursor-not-allowed'
                    : 'text-slate-400 hover:text-white hover:bg-white/5'
              }`}
              title={isRecording ? 'Stop recording' : isInitializing ? 'Initializing mic...' : 'Record voice input'}
            >
              {isRecording ? <MicOff className="w-4 h-4" /> : <Mic className="w-4 h-4" />}
            </button>

            {/* Send Button */}
            <button
              type="button"
              onClick={handleSend}
              disabled={loading || !input.trim()}
              className={`mb-2.5 mx-2.5 p-2 rounded-xl transition-all duration-300 shrink-0 ${
                input.trim() && !loading
                  ? 'bg-indigo-500 text-white shadow-lg shadow-indigo-500/25 hover:bg-indigo-600 hover:scale-105'
                  : 'bg-slate-800 text-slate-600 cursor-not-allowed'
              }`}
            >
              {loading ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Send className="w-4 h-4" />
              )}
            </button>
          </div>
        </div>

        {/* Micro-status indicators for Recording */}
        {isRecording && (
          <div className="flex items-center space-x-2 text-[10px] text-rose-400 bg-rose-500/5 border border-rose-500/10 px-3 py-1.5 rounded-xl font-medium w-max animate-pulse">
            <span className="w-1.5 h-1.5 rounded-full bg-rose-400 animate-ping"></span>
            <span>{recordingStatus}</span>
          </div>
        )}
      </footer>
    </div>
  );
}

export default Chat;
