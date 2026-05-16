'use client';

import { useCallback } from 'react';
import { useLanguageStore, type Language } from '@/stores/languageStore';
import zh from './zh.json';
import en from './en.json';
import th from './th.json';

type TranslationValue = string | Record<string, unknown>;
type Translations = Record<string, Record<string, TranslationValue>>;

const resources: Record<Language, Translations> = { zh, en, th };

function _get(obj: Translations, path: string): string {
  const keys = path.split('.');
  let current: unknown = obj;
  for (const key of keys) {
    if (current == null || typeof current !== 'object') return path;
    current = (current as Record<string, unknown>)[key];
  }
  return typeof current === 'string' ? current : path;
}

export type TFunction = (key: string, params?: Record<string, string | number>) => string;

/**
 * Translation hook. Usage:
 *   const { t } = useI18n();
 *   t('common.save')            → "保存" / "Save" / "บันทึก"
 *   t('common.total', { count: 5 }) → "共 5 条"
 */
export function useI18n() {
  const lang = useLanguageStore((s) => s.lang);

  const t: TFunction = useCallback(
    (key: string, params?: Record<string, string | number>) => {
      let text = _get(resources[lang] as Translations, key);
      if (params) {
        Object.entries(params).forEach(([k, v]) => {
          text = text.replace(`{${k}}`, String(v));
        });
      }
      return text;
    },
    [lang],
  );

  return { t, lang };
}

/** Get translation without hook (for non-component use) */
export function getTranslation(key: string, lang: Language, params?: Record<string, string | number>): string {
  let text = _get(resources[lang] as Translations, key);
  if (params) {
    Object.entries(params).forEach(([k, v]) => {
      text = text.replace(`{${k}}`, String(v));
    });
  }
  return text;
}

const langNames: Record<Language, string> = { zh: '中文', en: 'English', th: 'ไทย' };
export const languageOptions = Object.entries(langNames).map(([value, label]) => ({ value: value as Language, label }));
