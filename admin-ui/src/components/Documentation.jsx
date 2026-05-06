import React from 'react';
import { ArrowLeft, Mic, Cpu, Database, Activity, Zap, Shield, Server, Globe, Key, Network } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

const Documentation = () => {
    const navigate = useNavigate();

    return (
        <div className="h-full w-full bg-slate-50 text-slate-800 p-6 md:p-12 overflow-y-auto no-scrollbar relative">
            {/* Background elements */}
            <div className="fixed inset-0 overflow-hidden pointer-events-none -z-10">
                <div className="absolute top-0 left-1/4 w-96 h-96 bg-violet-600 rounded-full mix-blend-multiply filter blur-3xl opacity-10 animate-blob"></div>
                <div className="absolute top-0 right-1/4 w-96 h-96 bg-indigo-600 rounded-full mix-blend-multiply filter blur-3xl opacity-10 animate-blob animation-delay-2000"></div>
                <div className="absolute -bottom-32 left-1/3 w-96 h-96 bg-pink-600 rounded-full mix-blend-multiply filter blur-3xl opacity-10 animate-blob animation-delay-4000"></div>
            </div>

            <div className="max-w-5xl mx-auto">
                <button
                    onClick={() => navigate('/')}
                    className="flex items-center gap-2 text-slate-500 hover:text-indigo-600 transition-colors mb-8 group"
                >
                    <ArrowLeft className="w-5 h-5 group-hover:-translate-x-1 transition-transform" />
                    Back to Chat
                </button>

                <header className="mb-12 border-b border-indigo-100 pb-10">
                    <h1 className="text-4xl md:text-6xl font-black bg-clip-text text-transparent bg-gradient-to-r from-violet-700 to-indigo-600 mb-6 tracking-tight py-4 leading-normal">
                        TSM Crypto Intelligence
                    </h1>
                    <p className="text-xl md:text-2xl text-slate-600 max-w-3xl leading-relaxed">
                        A next-generation conversational AI interface designed for real-time cryptocurrency analysis, on-chain diagnostics, and market intelligence.
                    </p>
                </header>

                <section className="mb-16">
                    <h2 className="text-3xl font-bold text-slate-800 mb-8 flex items-center gap-3">
                        <Cpu className="w-8 h-8 text-violet-600" /> System Architecture
                    </h2>
                    <div className="bg-white/60 backdrop-blur-xl rounded-2xl p-8 border border-white/50 shadow-xl shadow-indigo-500/5 hover:shadow-indigo-500/10 transition-shadow">
                        <p className="text-lg text-slate-700 mb-6 leading-relaxed">
                            The TSM Crypto Chatbot operates on a decoupled <span className="font-bold">Microservices Architecture</span>. The frontend communicates via WebSockets for low-latency streaming, while the backend orchestrates a pipeline of specialized AI agents.
                        </p>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mt-8">
                            <div>
                                <h3 className="text-xl font-bold text-indigo-700 mb-3 flex items-center gap-2">
                                    <Server className="w-5 h-5" /> Backend Core
                                </h3>
                                <ul className="space-y-3 text-slate-600">
                                    <li className="flex items-start gap-2">
                                        <span className="w-2 h-2 mt-2 rounded-full bg-emerald-500 shrink-0"></span>
                                        <span><span className="font-bold">FastAPI Framework</span>: High-performance, asynchronous Python server handling requests.</span>
                                    </li>
                                    <li className="flex items-start gap-2">
                                        <span className="w-2 h-2 mt-2 rounded-full bg-emerald-500 shrink-0"></span>
                                        <span><span className="font-bold">Google ADK</span>: Orchestrates the "Root Crypto Agent" to manage tool calls and reasoning.</span>
                                    </li>
                                    <li className="flex items-start gap-2">
                                        <span className="w-2 h-2 mt-2 rounded-full bg-emerald-500 shrink-0"></span>
                                        <span><span className="font-bold">Gemini 2.5 Flash</span>: The cognitive engine ensuring context-aware, grounded responses.</span>
                                    </li>
                                </ul>
                            </div>
                            <div>
                                <h3 className="text-xl font-bold text-rose-600 mb-3 flex items-center gap-2">
                                    <Network className="w-5 h-5" /> Voice Pipeline
                                </h3>
                                <ul className="space-y-3 text-slate-600">
                                    <li className="flex items-start gap-2">
                                        <span className="w-2 h-2 mt-2 rounded-full bg-indigo-500 shrink-0"></span>
                                        <span><span className="font-bold">Input</span>: Web Speech API streams audio chunks to the backend.</span>
                                    </li>
                                    <li className="flex items-start gap-2">
                                        <span className="w-2 h-2 mt-2 rounded-full bg-indigo-500 shrink-0"></span>
                                        <span><span className="font-bold">STT (Speech-to-Text)</span>: OpenAI Whisper transcribes audio with near-human accuracy.</span>
                                    </li>
                                    <li className="flex items-start gap-2">
                                        <span className="w-2 h-2 mt-2 rounded-full bg-indigo-500 shrink-0"></span>
                                        <span><span className="font-bold">TTS (Text-to-Speech)</span>: Offline-capable engines generate natural-sounding voice responses instantly.</span>
                                    </li>
                                </ul>
                            </div>
                        </div>
                    </div>
                </section>

                <section className="mb-16">
                    <h2 className="text-3xl font-bold text-slate-800 mb-8 flex items-center gap-3">
                        <Activity className="w-8 h-8 text-emerald-600" /> Real-Time Intelligence
                    </h2>
                    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                        <FeatureCard
                            icon={<Globe className="text-blue-500" />}
                            title="Global Market Data"
                            description="Integrates with CoinMarketCap to pull sub-second price updates, 24h volume analytics, and liquidity scores."
                        />
                        <FeatureCard
                            icon={<Database className="text-orange-500" />}
                            title="On-Chain Diagnostics"
                            description="Queries Blockchair nodes to verify blockchain health, mempool congestion, and average miner fees."
                        />
                        <FeatureCard
                            icon={<Zap className="text-yellow-500" />}
                            title="Sentiment Analysis"
                            description="Aggregates breaking news from CryptoPanic and performs sentiment grading (Bullish/Bearish)."
                        />
                    </div>
                </section>

                <section className="mb-16">
                    <h2 className="text-3xl font-bold text-slate-800 mb-8 flex items-center gap-3">
                        <Key className="w-8 h-8 text-slate-600" /> Security & Privacy Protocol
                    </h2>
                    <div className="bg-white/60 backdrop-blur-xl rounded-2xl p-8 border border-white/50">
                        <p className="text-slate-600 leading-relaxed mb-4">
                            We prioritize user sovereignty. The TSM architecture ensures that:
                        </p>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                            <div className="bg-slate-50 p-6 rounded-xl border border-slate-100">
                                <h3 className="font-bold text-slate-800 mb-2 flex items-center gap-2"><Shield className="w-4 h-4 text-emerald-500" /> Ephemeral Processing</h3>
                                <p className="text-sm text-slate-500">Audio inputs are processed in-memory and discarded immediately after transcription. No user voice data is persisted to disk.</p>
                            </div>
                            <div className="bg-slate-50 p-6 rounded-xl border border-slate-100">
                                <h3 className="font-bold text-slate-800 mb-2 flex items-center gap-2"><Key className="w-4 h-4 text-violet-500" /> API Isolation</h3>
                                <p className="text-sm text-slate-500">External API keys (CMC, Blockchair) are managed via secure environment variables and never exposed to the client side.</p>
                            </div>
                        </div>
                    </div>
                </section>

                <section className="mb-12">
                    <h2 className="text-2xl font-bold text-slate-800 mb-6">Technologies Deployed</h2>
                    <div className="flex flex-wrap gap-3">
                        <TechBadge name="React 19" color="bg-blue-100 text-blue-700 hover:bg-blue-200" />
                        <TechBadge name="Vite Turbo" color="bg-purple-100 text-purple-700 hover:bg-purple-200" />
                        <TechBadge name="Tailwind v4" color="bg-cyan-100 text-cyan-700 hover:bg-cyan-200" />
                        <TechBadge name="FastAPI" color="bg-emerald-100 text-emerald-700 hover:bg-emerald-200" />
                        <TechBadge name="Google ADK" color="bg-indigo-100 text-indigo-700 hover:bg-indigo-200" />
                        <TechBadge name="Gemini 2.5 Flash" color="bg-orange-100 text-orange-700 hover:bg-orange-200" />
                        <TechBadge name="Whisper V3" color="bg-zinc-100 text-zinc-700 hover:bg-zinc-200" />
                    </div>
                </section>
            </div>
        </div>
    );
};

const FeatureCard = ({ icon, title, description }) => (
    <div className="bg-white/70 backdrop-blur-lg p-8 rounded-2xl border border-white/60 shadow-lg shadow-indigo-500/5 hover:-translate-y-1 hover:shadow-indigo-500/15 transition-all duration-300">
        <div className="bg-white w-14 h-14 rounded-2xl flex items-center justify-center shadow-sm mb-6">
            {React.cloneElement(icon, { size: 28 })}
        </div>
        <h3 className="text-xl font-bold text-slate-800 mb-3">{title}</h3>
        <p className="text-slate-500 leading-relaxed text-sm">{description}</p>
    </div>
);

const TechBadge = ({ name, color }) => (
    <span className={`px-4 py-1.5 rounded-full text-sm font-medium transition-colors cursor-default ${color}`}>
        {name}
    </span>
);

export default Documentation;
