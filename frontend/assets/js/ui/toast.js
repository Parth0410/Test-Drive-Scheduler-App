let hideTimer;

/** @param {'info' | 'success' | 'error'} variant */
export function showToast(message, variant = 'info') {
  const toast = document.querySelector('#toast');
  if (!toast) return;
  toast.textContent = message;
  toast.className = `toast ${variant}`;
  toast.hidden = false;
  clearTimeout(hideTimer);
  hideTimer = setTimeout(() => { toast.hidden = true; }, 3200);
}
