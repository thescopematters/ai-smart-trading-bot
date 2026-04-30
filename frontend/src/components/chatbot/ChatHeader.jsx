import { ChevronLeft, Book } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import tsmLogo from '../../assets/TSM-Logo.png';
import cryptobotAvatar from '../../assets/cryptobot_avatar_cute.png';

const ChatHeader = ({ onClose, onOpenHistory, status = 'Online' }) => {
    const navigate = useNavigate();

    return (
        <div className="flex items-center justify-between p-4 px-6 border-b border-indigo-50/50 bg-white/40 backdrop-blur-md">
            <div className="flex items-center gap-3">
                {onOpenHistory && (
                    <button 
                        onClick={onOpenHistory} 
                        className="p-2 -ml-2 rounded-full hover:bg-slate-100 transition text-slate-400 focus:outline-none"
                        title="Back to Chats"
                    >
                        <ChevronLeft className="w-5 h-5" />
                    </button>
                )}
                <div className="relative">
                    <div className="w-10 h-10 rounded-full overflow-hidden shadow-sm border border-slate-200 bg-white">
                        <img src={cryptobotAvatar} alt="CryptoBot" className="w-full h-full object-cover" />
                    </div>
                    <span className="absolute bottom-0 right-0 w-3 h-3 bg-emerald-400 border-2 border-white rounded-full"></span>
                </div>
                <div>
                    <h3
                        onClick={() => window.location.href = '/'}
                        className="font-bold text-slate-800 flex items-center gap-2 text-lg cursor-pointer hover:text-indigo-600 transition-colors"
                    >
                        CryptoBot
                    </h3>
                    <p className="text-xs text-slate-500 font-medium">{status}</p>
                </div>
            </div>

            <div className="flex items-center gap-4">
                <button
                    onClick={() => navigate('/docs')}
                    className="flex items-center gap-1 px-4 py-2 text-slate-500 hover:text-indigo-600 hover:bg-slate-100/50 rounded-full transition-all group"
                    title="Documentation"
                >
                    <Book className="w-5 h-5 group-hover:scale-110 transition-transform" />
                    <span className="font-bold text-sm hidden sm:block">Docs</span>
                </button>
                <div className="w-16 h-10 relative group">
                    <img
                        src={tsmLogo}
                        alt="TSM Logo"
                        className="w-full h-full object-contain opacity-80 group-hover:opacity-100 transition-opacity"
                    />
                </div>
            </div>
        </div>
    );
};

export default ChatHeader;
