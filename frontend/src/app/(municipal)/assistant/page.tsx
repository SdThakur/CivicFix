'use client';

import React, { useState } from 'react';
import { Bot, Send, User, Sparkles, AlertCircle, RefreshCw } from 'lucide-react';
import { assistantApi } from '@/lib/api';

export default function AssistantPage() {
  const [messages, setMessages] = useState([
    {
      sender: 'ai',
      text: 'Hello! I am the CivicFix Municipal AI Assistant powered by Gemini. Ask me about city infrastructure reports, hotspot trends, resolution SLAs, priority triage, or municipal workload statistics.',
    },
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSend = async (queryText?: string) => {
    const query = queryText || input;
    if (!query.trim()) return;

    const userMsg = { sender: 'user', text: query };
    setMessages((prev) => [...prev, userMsg]);
    if (!queryText) setInput('');
    setLoading(true);
    setError(null);

    try {
      // Query backend assistant API (Gemini function calling / DB queries)
      const res = await assistantApi.chat(query);
      setMessages((prev) => [
        ...prev,
        {
          sender: 'ai',
          text: res.reply || 'Analysis complete.',
        },
      ]);
    } catch (err: any) {
      setError('Unable to contact AI Assistant service. Ensure your GEMINI_API_KEY is configured in backend/.env.');
      setMessages((prev) => [
        ...prev,
        {
          sender: 'ai',
          text: 'I am currently having trouble reaching the AI service. Please verify your GEMINI_API_KEY configuration.',
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const sampleQuestions = [
    'What are the highest priority infrastructure problems right now?',
    'Which neighborhood has the most road hazards reported?',
    'What is the current average resolution time for potholes?',
    'How many active work orders are in the dispatch queue?',
  ];

  return (
    <div className="max-w-4xl mx-auto py-6 space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4 glass-panel p-6 rounded-2xl border border-slate-800">
        <div className="w-12 h-12 rounded-2xl bg-blue-600/20 border border-blue-500/40 flex items-center justify-center text-blue-400">
          <Bot className="w-7 h-7" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
            Municipal AI Staff Assistant
            <span className="text-xs px-2 py-0.5 rounded-full bg-blue-500/20 text-blue-400 font-semibold border border-blue-500/30">
              Live Gemini + DB Integration
            </span>
          </h1>
          <p className="text-slate-400 text-xs mt-0.5">
            Query real-time city infrastructure data, spatial stats, and resolution metrics in plain English.
          </p>
        </div>
      </div>

      {/* Error Alert */}
      {error && (
        <div className="flex items-center gap-3 p-4 rounded-2xl bg-rose-500/10 border border-rose-500/30 text-rose-400 text-sm">
          <AlertCircle className="w-5 h-5 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Chat Box */}
      <div className="glass-panel p-6 rounded-3xl border border-slate-800 space-y-6 min-h-[480px] flex flex-col justify-between">
        {/* Messages */}
        <div className="space-y-4 overflow-y-auto max-h-[420px] pr-2">
          {messages.map((m, idx) => (
            <div
              key={idx}
              className={`flex items-start gap-3 ${m.sender === 'user' ? 'flex-row-reverse' : ''}`}
            >
              <div className={`w-8 h-8 rounded-xl flex items-center justify-center flex-shrink-0 ${
                m.sender === 'user' ? 'bg-blue-600 text-white' : 'bg-slate-800 text-blue-400 border border-slate-700'
              }`}>
                {m.sender === 'user' ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
              </div>
              
              <div className={`p-4 rounded-2xl max-w-lg text-sm whitespace-pre-line leading-relaxed ${
                m.sender === 'user'
                  ? 'bg-blue-600 text-white font-medium'
                  : 'bg-slate-900/80 text-slate-200 border border-slate-800'
              }`}>
                {m.text}
              </div>
            </div>
          ))}

          {loading && (
            <div className="flex items-center gap-3 text-xs text-blue-400 font-medium">
              <Sparkles className="w-4 h-4 animate-spin" /> Querying database & analyzing spatial statistics...
            </div>
          )}
        </div>

        {/* Sample Suggestions */}
        <div className="pt-4 border-t border-slate-800/80 space-y-2">
          <span className="text-xs text-slate-400 font-medium block">Suggested Queries:</span>
          <div className="flex flex-wrap gap-2">
            {sampleQuestions.map((q, idx) => (
              <button
                key={idx}
                onClick={() => handleSend(q)}
                className="px-3 py-1.5 rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-800 text-xs text-slate-300 transition-colors text-left"
              >
                {q}
              </button>
            ))}
          </div>
        </div>

        {/* Input Bar */}
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSend();
          }}
          className="relative pt-2"
        >
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask assistant about city infrastructure data..."
            className="w-full pl-4 pr-12 py-3.5 rounded-2xl bg-slate-900 border border-slate-800 text-white text-sm focus:outline-none focus:border-blue-500 placeholder-slate-500"
          />
          <button
            type="submit"
            disabled={loading}
            className="absolute right-2.5 top-1/2 -translate-y-1/2 p-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white transition-colors disabled:opacity-50"
          >
            <Send className="w-4 h-4" />
          </button>
        </form>
      </div>
    </div>
  );
}
