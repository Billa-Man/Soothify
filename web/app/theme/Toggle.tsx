'use client';
import { useEffect, useState } from 'react';

export default function ThemeToggle() {
  const [ready, setReady] = useState(false);
  const [dark, setDark] = useState(false);

  useEffect(() => {
    const saved = typeof window !== 'undefined' ? localStorage.getItem('theme') : null;
    const isDark = saved ? saved === 'dark' : false;
    setDark(isDark);
    if (typeof document !== 'undefined') {
      const el = document.documentElement;
      el.classList.toggle('dark-theme', isDark);
      el.classList.toggle('light-theme', !isDark);
    }
    setReady(true);
  }, []);

  const toggle = () => {
    const next = !dark;
    setDark(next);
    if (typeof document !== 'undefined') {
      const el = document.documentElement;
      el.classList.toggle('dark-theme', next);
      el.classList.toggle('light-theme', !next);
    }
    if (typeof window !== 'undefined') {
      localStorage.setItem('theme', next ? 'dark' : 'light');
    }
  };

  if (!ready) return null;

  return (
    <button className="btn btn-outline" onClick={toggle} aria-label="Toggle theme">
      {dark ? 'Dark' : 'Light'}
    </button>
  );
}


