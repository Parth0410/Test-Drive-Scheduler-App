const FOCUSABLE = 'a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])';

let activeModal = null;
let returnFocusTo = null;

const focusableIn = (modal) => [...modal.querySelectorAll(FOCUSABLE)].filter((el) => el.offsetParent !== null);

export function openModal(modal, focusTarget) {
  if (activeModal && activeModal !== modal) closeModal(activeModal, { restoreFocus: false });
  else returnFocusTo = document.activeElement;

  activeModal = modal;
  modal.hidden = false;
  document.body.classList.add('modal-open');
  requestAnimationFrame(() => (focusTarget ?? focusableIn(modal)[0])?.focus());
}

export function closeModal(modal = activeModal, { restoreFocus = true } = {}) {
  if (!modal || modal.hidden) return;
  modal.hidden = true;
  if (modal === activeModal) activeModal = null;
  document.body.classList.remove('modal-open');
  if (restoreFocus) returnFocusTo?.focus?.();
}

function trapFocus(event) {
  if (!activeModal) return;
  if (event.key === 'Escape') {
    closeModal();
    return;
  }
  if (event.key !== 'Tab') return;

  const items = focusableIn(activeModal);
  if (!items.length) return;
  const first = items[0];
  const last = items[items.length - 1];
  if (event.shiftKey && document.activeElement === first) {
    event.preventDefault();
    last.focus();
  } else if (!event.shiftKey && document.activeElement === last) {
    event.preventDefault();
    first.focus();
  }
}

/** Wires close buttons, backdrop clicks, ESC and focus trapping for every .modal-backdrop. */
export function initModals() {
  document.querySelectorAll('[data-close-modal]').forEach((button) =>
    button.addEventListener('click', () => closeModal(button.closest('.modal-backdrop'))),
  );
  document.querySelectorAll('.modal-backdrop').forEach((backdrop) =>
    backdrop.addEventListener('mousedown', (event) => {
      if (event.target === backdrop) closeModal(backdrop);
    }),
  );
  document.addEventListener('keydown', trapFocus);
}
