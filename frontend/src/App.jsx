import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import Chat from './pages/Chat';
import History from './pages/History';

/**
 * Main App component configuring React Router and mapping core paths.
 * Integrates Sidebar component as a master layout wrapper.
 */
function App() {
  return (
    <Router>
      <div className="flex min-h-screen bg-slate-950 overflow-hidden">
        {/* Sidebar Layout */}
        <Sidebar />

        {/* Content Container */}
        <main className="flex-1 flex flex-col min-w-0 overflow-hidden relative">
          <Routes>
            {/* Interactive RAG chat query */}
            <Route path="/" element={<Chat />} />
            {/* User QA list log */}
            <Route path="/history" element={<History />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;
