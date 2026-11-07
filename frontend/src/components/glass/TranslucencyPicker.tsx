'use client';

import React, { useState, useEffect } from 'react';
import { Sun, Moon, Sliders } from 'lucide-react';

export default function TranslucencyPicker() {
  const [translucency, setTranslucency] = useState<'clear' | 'regular' | 'frosted'>('regular');
  const [theme, setTheme] = useState<'light' | 'dark'>('light');
  const [open, setOpen] = useState(false);

  useEffect(() => {
    const savedTrans = localStorage.getItem('civicfix_translucency') as any;
    if (savedTrans) {
      setTranslucency(savedTrans);
      document.documentElement.setAttribute('data-translucency', savedTrans);
    } else {
      document.documentElement.setAttribute('data-translucency', 'regular');
    }

    const savedTheme = localStorage.getItem('civicfix_theme') as any;
    if (savedTheme === 'dark') {
      setTheme('dark');
      document.documentElement.classList.add('dark');
      document.documentElement.setAttribute('data-theme', 'dark');
    } else {
      setTheme('light');
      document.documentElement.classList.remove('dark');
      document.documentElement.removeAttribute('data-theme');
    }
  }, []);

  const changeTranslucency = (val: 'clear' | 'regular' | 'frosted') => {
    setTranslucency(val);
    localStorage.setItem('civicfix_translucency', val);
    document.documentElement.setAttribute('data-translucency', val);
  };

  const toggleTheme = () => {
    const nextTheme = theme === 'light' ? 'dark' : 'light';
    setTheme(nextTheme);
    localStorage.setItem('civicfix_theme', nextTheme);
    if (nextTheme === 'dark') {
      document.documentElement.classList.add('dark');
      document.documentElement.setAttribute('data-theme', 'dark');
    } else {
      document.documentElement.classList.remove('dark');
      document.documentElement.removeAttribute('data-theme');
    }
  };

  return (
    <div className="relative">
      <button
        onClick={() => setOpen(!open)}
        title="Display & Translucency Preferences"
        className="min-h-[44px] min-w-[44px] p-2.5 rounded-xl text-content-secondary hover:text-content-primary hover:bg-neutral-black-06 active:scale-95 transition-all flex items-center justify-center"
        aria-label="Settings"
      >
        <Sliders className="w-4 h-4" />
      </button>

      {open && (
        <div className="absolute right-0 top-12 z-50 w-64 p-3 rounded-2xl liquid-glass-surface specular-edge shadow-floating border border-surface-border space-y-3 animate-in fade-in zoom-in-95 duration-fast">
          <div className="flex items-center justify-between pb-2 border-b border-surface-border">
            <span className="text-xs font-bold text-content-primary">Theme & Glass</span>
            <button
              onClick={toggleTheme}
              className="px-2.5 py-1 rounded-lg text-xs font-semibold flex items-center gap-1.5 bg-neutral-black-06 hover:bg-neutral-black-12 text-content-primary transition-colors"
            >
              {theme === 'light' ? (
                <>
                  <Moon className="w-3.5 h-3.5 text-md-black" />
                  Dark
                </>
              ) : (
                <>
                  <Sun className="w-3.5 h-3.5 text-md-gold" />
                  Light
                </>
              )}
            </button>
          </div>

          <div>
            <label className="text-[11px] font-bold text-content-secondary uppercase tracking-wider block mb-1.5">
              Glass Translucency
            </label>
            <div className="grid grid-cols-3 gap-1 p-1 rounded-xl bg-neutral-black-06">
              {(['clear', 'regular', 'frosted'] as const).map((mode) => (
                <button
                  key={mode}
                  onClick={() => changeTranslucency(mode)}
                  className={`py-1.5 text-xs font-bold rounded-lg capitalize transition-all ${
                    translucency === mode
                      ? 'liquid-glass-gold shadow-sm'
                      : 'text-content-secondary hover:text-content-primary'
                  }`}
                >
                  {mode}
                </button>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

