import { NavLink } from 'react-router-dom';
import { 
  MessageSquare, 
  History,
  Sparkles
} from 'lucide-react';

/**
 * Reusable Sidebar Navigation Component.
 * Contains links for Chat and History.
 */
function Sidebar() {
  const navItems = [
    { name: 'Chat', path: '/', icon: MessageSquare },
    { name: 'History', path: '/history', icon: History }
  ];

  return (
    <aside className="w-64 glass-panel border-r border-white/5 min-h-screen p-6 flex flex-col justify-between shrink-0">
      <div className="space-y-8">
        {/* Brand Header */}
        <div className="flex items-center space-x-3 px-2">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-500 to-cyan-400 flex items-center justify-center shadow-lg shadow-indigo-500/20">
            <Sparkles className="w-5 h-5 text-white" />
          </div>
          <div>
            <h2 className="font-bold text-white text-base tracking-wide leading-tight">DocMind AI</h2>
            <span className="text-[10px] text-indigo-400 font-semibold uppercase tracking-wider">RAG Assistant</span>
          </div>
        </div>

        {/* Navigation Items */}
        <nav className="space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.name}
                to={item.path}
                className={({ isActive }) => 
                  `flex items-center space-x-3 px-4 py-3 rounded-xl text-sm font-medium transition-all duration-200 ${
                    isActive 
                      ? 'bg-gradient-to-r from-indigo-500/15 to-indigo-500/5 text-indigo-400 border border-indigo-500/20' 
                      : 'text-slate-400 hover:text-white hover:bg-white/5 border border-transparent'
                  }`
                }
              >
                <Icon className="w-4 h-4" />
                <span>{item.name}</span>
              </NavLink>
            );
          })}
        </nav>
      </div>

      {/* Footer Branding */}
      <div className="border-t border-white/5 pt-4 px-2">
        <p className="text-[10px] text-slate-500 tracking-wide">Version 1.0.0</p>
        <p className="text-[10px] text-slate-600">DocMind AI © 2026</p>
      </div>
    </aside>
  );
}

export default Sidebar;
