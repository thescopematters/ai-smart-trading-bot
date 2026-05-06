import { ChevronLeft } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import cryptobotAvatar from '../../assets/cryptobot_avatar_cute.png';

const ChatHeader = ({ onClose, onOpenHistory, status = 'Online', showHistoryBtn = true }) => {
    const navigate = useNavigate();

    return (
        <div className="flex items-center justify-between p-4 px-6 border-b border-indigo-50/50 bg-white/40 backdrop-blur-md">
            <div className="flex items-center gap-3">
                {onOpenHistory && showHistoryBtn && (
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
                {/* Removed Docs and TSM Logo as requested */}
            </div>
        </div>
    );
};

export default ChatHeader;
