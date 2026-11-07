'use client';

import React, { createContext, useContext, useState, useEffect } from 'react';

export type Language = 'en' | 'es';

interface Translations {
  [key: string]: {
    en: string;
    es: string;
  };
}

const DICTIONARY: Translations = {
  // Navigation
  'nav.home': { en: 'Home', es: 'Inicio' },
  'nav.map': { en: 'Public Map', es: 'Mapa Público' },
  'nav.report': { en: 'Report Hazard', es: 'Reportar Peligro' },
  'nav.dashboard': { en: 'Dashboard', es: 'Panel' },
  'nav.transparency': { en: 'Transparency', es: 'Transparencia' },
  'nav.signIn': { en: 'Sign In', es: 'Iniciar Sesión' },
  'nav.register': { en: 'Register', es: 'Registrarse' },

  // Statuses
  'status.submitted': { en: 'Submitted', es: 'Enviado' },
  'status.in_progress': { en: 'In Progress', es: 'En Progreso' },
  'status.resolved': { en: 'Resolved', es: 'Resuelto' },
  'status.critical': { en: 'Critical Priority', es: 'Prioridad Crítica' },

  // Actions
  'action.tryAgain': { en: 'Try Again', es: 'Reintentar' },
  'action.refresh': { en: 'Refresh', es: 'Actualizar' },
  'action.search': { en: 'Search', es: 'Buscar' },
  'action.submit': { en: 'Submit Report', es: 'Enviar Reporte' },
  'action.upvote': { en: 'Upvote Report', es: 'Apoyar Reporte' },
  'action.locateOnMap': { en: 'View on Map', es: 'Ver en Mapa' },

  // Skeletons and Empty States
  'empty.noReports': { en: 'No infrastructure incidents found', es: 'No se encontraron incidentes de infraestructura' },
  'empty.noReportsDesc': { en: 'Photograph any road hazard or street damage to trigger automated AI classification.', es: 'Fotografíe cualquier peligro vial o daño para activar la clasificación automática de IA.' },
  'empty.clearFilters': { en: 'Clear all filters', es: 'Restablecer filtros' },

  // Toast notices
  'toast.copied': { en: 'Link copied to clipboard', es: 'Enlace copiado al portapapeles' },
  'toast.prefsSaved': { en: 'Notification preferences updated', es: 'Preferencias de notificación actualizadas' },
};

interface I18nContextType {
  lang: Language;
  setLang: (lang: Language) => void;
  t: (key: string) => string;
}

const I18nContext = createContext<I18nContextType>({
  lang: 'en',
  setLang: () => {},
  t: (key) => key,
});

export function I18nProvider({ children }: { children: React.ReactNode }) {
  const [lang, setLangState] = useState<Language>('en');

  useEffect(() => {
    try {
      const stored = localStorage.getItem('civicfix_lang') as Language;
      if (stored === 'en' || stored === 'es') {
        setLangState(stored);
      }
    } catch {}
  }, []);

  const setLang = (newLang: Language) => {
    setLangState(newLang);
    try {
      localStorage.setItem('civicfix_lang', newLang);
      document.documentElement.lang = newLang;
    } catch {}
  };

  const t = (key: string): string => {
    if (DICTIONARY[key]) {
      return DICTIONARY[key][lang] || DICTIONARY[key].en;
    }
    return key;
  };

  return (
    <I18nContext.Provider value={{ lang, setLang, t }}>
      {children}
    </I18nContext.Provider>
  );
}

export function useI18n() {
  return useContext(I18nContext);
}

