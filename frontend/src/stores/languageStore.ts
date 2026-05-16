import { create } from 'zustand';

export type Language = 'zh' | 'en' | 'th';

const STORAGE_KEY = 'thaiestate_lang';

function getInitialLang(): Language {
  if (typeof window === 'undefined') return 'zh';
  const stored = localStorage.getItem(STORAGE_KEY);
  if (stored === 'zh' || stored === 'en' || stored === 'th') return stored;
  // Detect browser language
  const nav = navigator.language?.toLowerCase() || '';
  if (nav.startsWith('th')) return 'th';
  if (nav.startsWith('en')) return 'en';
  return 'zh';
}

interface LanguageState {
  lang: Language;
  setLang: (lang: Language) => void;
}

export const useLanguageStore = create<LanguageState>((set) => ({
  lang: getInitialLang(),
  setLang: (lang: Language) => {
    localStorage.setItem(STORAGE_KEY, lang);
    set({ lang });
  },
}));
