import { useState, useEffect } from 'react';
import { 
  Search, 
  Trash2, 
  Calendar, 
  ChevronLeft, 
  ChevronRight, 
  MessageSquare,
  FileText,
  Sparkles
} from 'lucide-react';

/**
 * History Page Component.
 * Fetches query history cache from local storage and adds:
 * - Text search queries (for questions and answers)
 * - Pagination (5 items per page)
 * - Delete actions (clear single item or wipe entire list)
 */
function History() {
  const [history, setHistory] = useState([]);
  const [search, setSearch] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 5;

  // Load history from local storage
  const loadHistory = () => {
    const cachedHistory = JSON.parse(localStorage.getItem('docmind_query_history') || '[]');
    setHistory(cachedHistory);
  };

  useEffect(() => {
    loadHistory();
  }, []);

  // Delete a single history entry
  const handleDeleteItem = (id) => {
    if (window.confirm('Delete this history entry?')) {
      const updated = history.filter(item => item.id !== id);
      localStorage.setItem('docmind_query_history', JSON.stringify(updated));
      setHistory(updated);
      // Adjust current page if empty after deletion
      const maxPage = Math.ceil(updated.length / itemsPerPage) || 1;
      if (currentPage > maxPage) {
        setCurrentPage(maxPage);
      }
    }
  };

  // Clear all history entries
  const handleClearAll = () => {
    if (window.confirm('Are you sure you want to clear your entire question history? This cannot be undone.')) {
      localStorage.setItem('docmind_query_history', '[]');
      setHistory([]);
      setCurrentPage(1);
    }
  };

  // Filter history based on search query (case-insensitive)
  const filteredHistory = history.filter(item => 
    item.question.toLowerCase().includes(search.toLowerCase()) ||
    item.answer.toLowerCase().includes(search.toLowerCase())
  );

  // Pagination logic
  const totalPages = Math.ceil(filteredHistory.length / itemsPerPage) || 1;
  const startIndex = (currentPage - 1) * itemsPerPage;
  const paginatedItems = filteredHistory.slice(startIndex, startIndex + itemsPerPage);

  const goToNextPage = () => {
    if (currentPage < totalPages) setCurrentPage(currentPage + 1);
  };

  const goToPrevPage = () => {
    if (currentPage > 1) setCurrentPage(currentPage - 1);
  };

  return (
    <div className="flex-1 p-8 bg-slate-950 overflow-y-auto space-y-8 relative">
      {/* Background glow spots */}
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-indigo-600/5 rounded-full blur-3xl pointer-events-none"></div>
      <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-cyan-500/5 rounded-full blur-3xl pointer-events-none"></div>

      <div className="max-w-4xl mx-auto space-y-6 relative z-10">
        
        {/* Header Section */}
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-extrabold text-white">Conversation History</h1>
            <p className="text-slate-400 text-sm mt-1">Review past questions, answers, and source citations.</p>
          </div>
          {history.length > 0 && (
            <button
              onClick={handleClearAll}
              className="flex items-center space-x-2 text-xs text-rose-400 hover:text-rose-300 px-3.5 py-2 bg-rose-500/5 hover:bg-rose-500/10 border border-rose-500/10 hover:border-rose-500/20 rounded-xl transition-all duration-200"
            >
              <Trash2 className="w-3.5 h-3.5" />
              <span>Wipe History</span>
            </button>
          )}
        </div>

        {/* Search Bar Panel */}
        <div className="relative">
          <Search className="absolute left-4 top-3.5 w-4 h-4 text-slate-500" />
          <input
            type="text"
            placeholder="Search questions or answers..."
            value={search}
            onChange={(e) => { setSearch(e.target.value); setCurrentPage(1); }}
            className="w-full bg-slate-900 border border-white/5 focus:border-indigo-500/40 rounded-2xl pl-11 pr-5 py-3.5 text-sm text-slate-200 placeholder-slate-500 focus:outline-none resize-none shadow-xl focus:ring-1 focus:ring-indigo-500/25 transition-all duration-200"
          />
        </div>

        {/* History Item Cards List */}
        {paginatedItems.length === 0 ? (
          <div className="glass-panel border border-white/5 rounded-3xl p-12 text-center text-slate-500 text-sm">
            {search ? 'No history entries match your search criteria.' : 'Your conversation history is currently empty.'}
          </div>
        ) : (
          <div className="space-y-4">
            {paginatedItems.map((item) => (
              <div 
                key={item.id} 
                className="glass-panel border border-white/5 rounded-2xl p-6 shadow-md relative group hover:border-indigo-500/10 transition-all duration-200"
              >
                {/* Delete button (displays on card hover) */}
                <button
                  onClick={() => handleDeleteItem(item.id)}
                  className="absolute right-6 top-6 p-2 rounded-xl bg-slate-900 border border-white/5 text-slate-500 hover:text-rose-400 hover:border-rose-500/20 opacity-0 group-hover:opacity-100 transition-all duration-200"
                  title="Delete Entry"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>

                {/* Content */}
                <div className="space-y-4 max-w-[90%]">
                  {/* Timestamp Header */}
                  <div className="flex items-center space-x-2 text-[10px] text-slate-500">
                    <Calendar className="w-3.5 h-3.5 text-indigo-400" />
                    <span>{new Date(item.timestamp).toLocaleString()}</span>
                  </div>

                  {/* Question */}
                  <div className="space-y-1">
                    <span className="text-[10px] text-indigo-400 font-semibold uppercase tracking-wider block">Question:</span>
                    <p className="text-xs font-semibold text-slate-200">{item.question}</p>
                  </div>

                  {/* Answer */}
                  <div className="space-y-1">
                    <span className="text-[10px] text-cyan-400 font-semibold uppercase tracking-wider block">Answer:</span>
                    <p className="text-xs text-slate-300 leading-relaxed whitespace-pre-wrap">{item.answer}</p>
                  </div>

                  {/* Source citations */}
                  {item.sources && item.sources.length > 0 && (
                    <div className="pt-2 border-t border-white/5 flex flex-wrap gap-2">
                      {item.sources.map((src, index) => (
                        <div 
                          key={index}
                          className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-slate-900 border border-white/5 text-[10px] text-slate-400"
                        >
                          <FileText className="w-2.5 h-2.5 text-indigo-400 shrink-0" />
                          <span className="max-w-[120px] truncate">{src.source || 'Document'}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ))}

            {/* Pagination Controls */}
            {totalPages > 1 && (
              <div className="flex justify-between items-center pt-4">
                <span className="text-xs text-slate-500 font-medium">
                  Page {currentPage} of {totalPages}
                </span>
                <div className="flex space-x-2">
                  <button
                    onClick={goToPrevPage}
                    disabled={currentPage === 1}
                    className={`p-2 rounded-xl border border-white/5 ${
                      currentPage === 1 
                        ? 'bg-slate-950 text-slate-700 cursor-not-allowed' 
                        : 'bg-slate-900 text-slate-400 hover:text-white hover:border-indigo-500/20'
                    } transition-colors`}
                  >
                    <ChevronLeft className="w-4 h-4" />
                  </button>
                  <button
                    onClick={goToNextPage}
                    disabled={currentPage === totalPages}
                    className={`p-2 rounded-xl border border-white/5 ${
                      currentPage === totalPages 
                        ? 'bg-slate-950 text-slate-700 cursor-not-allowed' 
                        : 'bg-slate-900 text-slate-400 hover:text-white hover:border-indigo-500/20'
                    } transition-colors`}
                  >
                    <ChevronRight className="w-4 h-4" />
                  </button>
                </div>
              </div>
            )}
          </div>
        )}

      </div>
    </div>
  );
}

export default History;
