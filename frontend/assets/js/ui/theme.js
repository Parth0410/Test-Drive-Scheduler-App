import { icons } from '../core/icons.js';

const STORAGE_KEY = 'theme';
const root = document.documentElement;

function applyTheme(theme) {
  root.dataset.theme = theme;
  const toggle = document.querySelector('[data-theme-toggle]');
  if (!toggle) return;
  const isDark = theme === 'dark';
  toggle.innerHTML = isDark ? icons.sun() : icons.moon();
  toggle.setAttribute('aria-label', isDark ? 'Switch to light theme' : 'Switch to dark theme');
  toggle.setAttribute('aria-pressed', String(!isDark));
}

export function initTheme() {
  applyTheme(localStorage.getItem(STORAGE_KEY) === 'light' ? 'light' : 'dark');
  document.querySelector('[data-theme-toggle]')?.addEventListener('click', () => {
    const next = root.dataset.theme === 'dark' ? 'light' : 'dark';
    localStorage.setItem(STORAGE_KEY, next);
    applyTheme(next);
  });
}
