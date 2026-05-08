/* eslint-disable no-unused-vars */

import { ChevronLeft, Maximize2, Minimize2, X } from 'lucide-react';
import cryptobotAvatar from '../../assets/cryptobot_avatar_cute.png';

const ChatHeader = ({ onClose, onOpenHistory, status = 'Online', showHistoryBtn = true, onMaximize, isMaximized }) => {
    return (
        <div className="flex items-center justify-between p-4 px-6 border-b border-indigo-50/50 bg-white/40 backdrop-blur-md">
            <div className="flex items-center gap-3">
                {onOpenHistory && showHistoryBtn && (
                    <button onClick={onOpenHistory} className="p-2 -ml-2 rounded-full hover:bg-slate-100 transition text-slate-400">
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
                    <h3 onClick={() => window.location.href = '/'}
                        className="font-bold text-slate-800 text-lg cursor-pointer hover:text-indigo-600 transition-colors">
                        CryptoBot
                    </h3>
                    <p className="text-xs text-slate-500 font-medium">{status}</p>
                </div>
            </div>

            {/* RIGHT SIDE - maximize button right of everything */}
            {onMaximize && (
                <button
                    onClick={onMaximize}
                    className="p-3.5 rounded-xl bg-slate-900 text-white hover:bg-black flex items-center justify-center transition-all"
                    title={isMaximized ? 'Minimize' : 'Maximize'}
                >
                    {isMaximized ? <Minimize2 className="w-4 h-4" /> : <Maximize2 className="w-4 h-4" />}
                </button>
            )}
        </div>
    );
};

export default ChatHeader;