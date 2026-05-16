'use client';

import { Select } from 'antd';
import { GlobalOutlined } from '@ant-design/icons';
import { languageOptions } from '@/i18n/i18n';
import { useLanguageStore, type Language } from '@/stores/languageStore';

export default function LanguageSwitcher() {
  const lang = useLanguageStore((s) => s.lang);
  const setLang = useLanguageStore((s) => s.setLang);

  return (
    <Select
      value={lang}
      onChange={(v: Language) => setLang(v)}
      options={languageOptions}
      size="small"
      popupMatchSelectWidth={false}
      style={{ width: 100 }}
      prefix={<GlobalOutlined />}
    />
  );
}
