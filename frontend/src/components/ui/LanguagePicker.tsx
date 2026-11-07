'use client';

import React from 'react';
import { Globe } from 'lucide-react';
import { useI18n, Language } from '@/lib/i18n';

export default function LanguagePicker() {
  const { lang, setLang } = useI18n();

  return (
    <div 
      className="inline-flex items-center p-1 rounded-xl liquid-glass-surface specular-edge border border-surface-border text-xs font-bold"
      role="group"
      aria-label="Language selector"
    >
      <Globe className="w-3.5 h-3.5 text-content-secondary ml-1 mr-1" />
      <button
        onClick={() => setLang('en')}
        className={`px-2 py-1 rounded-lg transition-all min-h-[32px] ${
          lang === 'en'
            ? 'liquid-glass-gold font-black text-md-black shadow-sm'
            : 'text-content-secondary hover:text-content-primary'
        }`}
        aria-pressed={lang === 'en'}
        aria-label="English language"
      >
        EN
      </button>
      <button
        onClick={() => setLang('es')}
        className={`px-2 py-1 rounded-lg transition-all min-h-[32px] ${
          lang === 'es'
            ? 'liquid-glass-gold font-black text-md-black shadow-sm'
            : 'text-content-secondary hover:text-content-primary'
        }`}
        aria-pressed={lang === 'es'}
        aria-label="Idioma español"
      >
        ES
      </button>
    </div>
  );
}

