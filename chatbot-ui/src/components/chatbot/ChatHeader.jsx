/* eslint-disable no-unused-vars */

import { ChevronLeft, Maximize2, Minimize2, X, Volume2, VolumeX } from 'lucide-react';
import cryptobotAvatar from '../../assets/cryptobot_avatar_cute_1.png';

const ChatHeader = ({ onClose, onOpenHistory, status = 'Online', showHistoryBtn = true, onMaximize, isMaximized, ttsEnabled, onToggleTts }) => {
    return (
        <div className="flex items-center justify-between p-3 px-3 sm:p-4 sm:px-4 border-b border-slate-700 bg-[#072042] backdrop-blur-md">
            <div className="flex items-center gap-3">
                {onOpenHistory && showHistoryBtn && (
                    <button onClick={onOpenHistory} className="p-2 -ml-2 rounded-full hover:bg-white/10 transition text-slate-300">
                        <ChevronLeft className="w-5 h-5" />
                    </button>
                )}
                <div className="relative">
                    <div className="w-10 h-10 rounded-full overflow-hidden shadow-sm border-2 border-slate-200 bg-white">
                        <img src={cryptobotAvatar} alt="CryptoBot" className="w-full h-full object-cover" />
                    </div>
                    <span className="absolute bottom-0 right-0 w-3 h-3 bg-emerald-400 border-2 border-white rounded-full"></span>
                </div>
                <div>
                    <h3 onClick={() => window.location.href = '/'}
                        className="font-bold text-white text-lg cursor-pointer transition-colors">
                        CryptoBot
                    </h3>
                    <p className="text-xs text-slate-300 font-medium">{status}</p>
                </div>
            </div>

            {/* RIGHT SIDE - maximize button right of everything */}
            <div className="flex items-center gap-2">
                <button
                    onClick={onClose}
                    className="p-3.5 rounded-xl bg-slate-900 text-white hover:bg-black flex sm:hidden items-center justify-center transition-all"
                    title="Close"
                >
                    <X className="w-4 h-4" />
                </button>

                {onToggleTts && (
                    <button
                        onClick={onToggleTts}
                        className="p-2 rounded-full hover:bg-white/10 transition text-white flex items-center justify-center"
                        title={ttsEnabled ? 'Disable voice answers' : 'Enable voice answers'}
                    >
                        {ttsEnabled ? <Volume2 className="w-4 h-4" /> : <VolumeX className="w-4 h-4 text-slate-400" />}
                    </button>
                )}

                {onMaximize && (
                    <button
                    onClick={onMaximize}
                    className="p-2 rounded-full hover:bg-white/10 transition text-white flex items-center justify-center"
                    title={isMaximized ? 'Minimize' : 'Maximize'}
                    >
                    {isMaximized ? <Minimize2 className="w-4 h-4" /> : <Maximize2 className="w-4 h-4" />}
                    </button>
                )}
            </div>
        </div>
    );
};

export default ChatHeader;